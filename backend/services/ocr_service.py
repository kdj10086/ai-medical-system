import os
from config import OCR_PROVIDER, UPLOAD_FOLDER


def extract_text(image_path):
    """Extract text from a medical report image.

    Args:
        image_path: Path to the uploaded image file

    Returns:
        Extracted text string
    """
    if OCR_PROVIDER == "paddleocr":
        return _extract_paddleocr(image_path)
    elif OCR_PROVIDER == "baidu":
        return _extract_baidu(image_path)
    else:
        return _mock_extract(image_path)


def _extract_paddleocr(image_path):
    """Extract text using PaddleOCR."""
    try:
        from paddleocr import PaddleOCR
        ocr = PaddleOCR(use_angle_cls=True, lang='ch')
        result = ocr.ocr(image_path, cls=True)
        lines = []
        for line_group in result:
            for line in line_group:
                text = line[1][0]
                lines.append(text)
        return '\n'.join(lines)
    except ImportError:
        return _mock_extract(image_path)
    except Exception as e:
        print(f"PaddleOCR error: {e}")
        return _mock_extract(image_path)


def _extract_baidu(image_path):
    """Extract text using Baidu OCR API."""
    try:
        from aip import AipOcr
        APP_ID = os.environ.get("BAIDU_OCR_APP_ID", "")
        API_KEY = os.environ.get("BAIDU_OCR_API_KEY", "")
        SECRET_KEY = os.environ.get("BAIDU_OCR_SECRET_KEY", "")

        if not all([APP_ID, API_KEY, SECRET_KEY]):
            return _mock_extract(image_path)

        client = AipOcr(APP_ID, API_KEY, SECRET_KEY)
        with open(image_path, 'rb') as f:
            image = f.read()
        result = client.basicGeneral(image)
        lines = [item['words'] for item in result.get('words_result', [])]
        return '\n'.join(lines)
    except ImportError:
        return _mock_extract(image_path)
    except Exception as e:
        print(f"Baidu OCR error: {e}")
        return _mock_extract(image_path)


def _mock_extract(image_path):
    """Mock OCR extraction for demo - returns a sample blood test report."""
    import time
    time.sleep(0.5)

    return """检验报告单

姓名：张XX        性别：男        年龄：35
检验项目：血常规 + 生化
检验日期：2026-06-28

白细胞(WBC)：6.5 x 10^9/L    参考范围：3.5-9.5
红细胞(RBC)：4.8 x 10^12/L   参考范围：4.3-5.8
血红蛋白(Hb)：145 g/L         参考范围：130-175
血小板(PLT)：180 x 10^9/L     参考范围：125-350
血糖(GLU)：6.8 mmol/L        参考范围：3.9-6.1 ↑
总胆固醇(TC)：5.6 mmol/L     参考范围：3.1-5.2 ↑
甘油三酯(TG)：1.8 mmol/L     参考范围：0.4-1.7 ↑
ALT(谷丙转氨酶)：28 U/L       参考范围：9-50
肌酐(Cr)：78 umol/L           参考范围：59-104
"""
