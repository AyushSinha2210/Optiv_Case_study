"""Optical Character Recognition (OCR) engine with confidence scoring and preprocessing."""

import concurrent.futures
from abc import ABC, abstractmethod
from typing import Optional, Tuple, List, Dict, Any
from pydantic import BaseModel, Field
from PIL import Image
import numpy as np

from .config import IngestionConfig
from .schemas import WarningInfo


class OCRResult(BaseModel):
    """Result of OCR extraction for a single image/page."""
    text: str
    confidence: Optional[float] = None
    warnings: List[WarningInfo] = Field(default_factory=list)
    method_used: str = "ocr"


class BaseOCREngine(ABC):
    """Abstract interface for swappable OCR backends."""

    @abstractmethod
    def process_image(
        self, image: Image.Image, page_num: int, config: IngestionConfig
    ) -> OCRResult:
        """Run OCR on the given image and return structured text and confidence."""
        pass


def preprocess_image_for_ocr(image: Image.Image) -> Image.Image:
    """Apply light OpenCV preprocessing (grayscale, deskew, thresholding) for low-confidence images."""
    import cv2

    np_img = np.array(image)

    # 1. Grayscale
    if len(np_img.shape) == 3:
        gray = cv2.cvtColor(np_img, cv2.COLOR_RGB2GRAY)
    else:
        gray = np_img

    # 2. Deskew calculation
    try:
        coords = np.column_stack(np.where(gray < 240))
        if coords.size > 0:
            angle = cv2.minAreaRect(coords)[-1]
            if angle < -45:
                angle = -(90 + angle)
            elif angle > 45:
                angle = 90 - angle
            if abs(angle) > 0.5:
                (h, w) = gray.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, angle, 1.0)
                gray = cv2.warpAffine(
                    gray, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
                )
    except Exception:
        pass  # Deskew failure should never crash OCR

    # 3. Adaptive threshold / Otsu binarization
    try:
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return Image.fromarray(thresh)
    except Exception:
        return Image.fromarray(gray)


class TesseractEngine(BaseOCREngine):
    """Production Tesseract OCR engine with fast-path and adaptive fallback."""

    def __init__(self, tesseract_cmd: Optional[str] = None):
        import pytesseract
        self.pytesseract = pytesseract
        if tesseract_cmd:
            self.pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    def _calculate_confidence_and_text(
        self, image: Image.Image
    ) -> Tuple[str, Optional[float]]:
        """Run Tesseract image_to_data and compute mean confidence over extracted words."""
        try:
            data = self.pytesseract.image_to_data(
                image, output_type=self.pytesseract.Output.DICT
            )
            words = []
            confidences = []
            n_boxes = len(data["text"])
            for i in range(n_boxes):
                word = data["text"][i].strip()
                conf_val = float(data["conf"][i])
                if word and conf_val >= 0:
                    words.append(word)
                    confidences.append(conf_val)

            full_text = self.pytesseract.image_to_string(image).strip()
            mean_conf = (
                sum(confidences) / len(confidences) if confidences else None
            )
            return full_text, mean_conf
        except Exception:
            return "", None

    def process_image(
        self, image: Image.Image, page_num: int, config: IngestionConfig
    ) -> OCRResult:
        warnings: List[WarningInfo] = []

        # Handle page rotation / OSD if needed
        try:
            osd = self.pytesseract.image_to_osd(image, output_type=self.pytesseract.Output.DICT)
            rotation = osd.get("rotate", 0)
            if rotation in (90, 180, 270):
                image = image.rotate(-rotation, expand=True)
        except Exception:
            pass  # OSD is best-effort

        # 1. Fast path: run OCR on raw rendered image
        text, conf = self._calculate_confidence_and_text(image)

        # 2. Check if confidence is below threshold
        if conf is not None and conf < config.ocr_confidence_threshold:
            # Apply OpenCV enhancement
            enhanced_image = preprocess_image_for_ocr(image)
            enhanced_text, enhanced_conf = self._calculate_confidence_and_text(enhanced_image)

            # Keep enhanced version if it improved confidence or extracted more text
            if enhanced_conf is not None and (conf is None or enhanced_conf > conf):
                text, conf = enhanced_text, enhanced_conf

            # If confidence is still low after enhancement, flag safe warning
            if conf is not None and conf < config.ocr_confidence_threshold:
                warnings.append(
                    WarningInfo(
                        code="WARN_OCR_LOW_CONFIDENCE",
                        page=page_num,
                        message=f"Mean OCR confidence ({conf:.1f}%) is below quality threshold",
                    )
                )

        if not text:
            warnings.append(
                WarningInfo(
                    code="WARN_OCR_NO_TEXT",
                    page=page_num,
                    message="OCR extraction yielded no recognizable textual content",
                )
            )

        return OCRResult(
            text=text,
            confidence=conf,
            warnings=warnings,
            method_used="ocr",
        )


class RapidOCREngine(BaseOCREngine):
    """Alternative lightweight ONNX OCR engine."""

    def __init__(self):
        from rapidocr_onnxruntime import RapidOCR
        self.engine = RapidOCR()

    def process_image(
        self, image: Image.Image, page_num: int, config: IngestionConfig
    ) -> OCRResult:
        warnings: List[WarningInfo] = []
        try:
            np_img = np.array(image)
            result, _ = self.engine(np_img)
            if not result:
                return OCRResult(
                    text="",
                    confidence=None,
                    warnings=[
                        WarningInfo(
                            code="WARN_OCR_NO_TEXT",
                            page=page_num,
                            message="RapidOCR detected no text on page",
                        )
                    ],
                )

            texts = [item[1] for item in result]
            scores = [float(item[2]) * 100.0 for item in result]
            mean_conf = sum(scores) / len(scores) if scores else None
            full_text = "\n".join(texts)

            if mean_conf is not None and mean_conf < config.ocr_confidence_threshold:
                warnings.append(
                    WarningInfo(
                        code="WARN_OCR_LOW_CONFIDENCE",
                        page=page_num,
                        message=f"Mean OCR confidence ({mean_conf:.1f}%) is below quality threshold",
                    )
                )

            return OCRResult(text=full_text, confidence=mean_conf, warnings=warnings)
        except Exception as e:
            return OCRResult(
                text="",
                confidence=None,
                warnings=[
                    WarningInfo(
                        code="ERR_OCR_FAILED",
                        page=page_num,
                        message="RapidOCR engine failure during execution",
                    )
                ],
            )


def get_ocr_engine(config: IngestionConfig) -> BaseOCREngine:
    """Factory creating the configured OCR engine."""
    if config.ocr_engine.lower() == "rapidocr":
        return RapidOCREngine()
    return TesseractEngine(tesseract_cmd=config.tesseract_cmd)
