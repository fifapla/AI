from typing import Dict, Any

class ModelQuantizer:
    def __init__(self, target_precision: str = "INT8"):
        self.target_precision = target_precision

    def quantize_weights(self, original_size_mb: float) -> Dict[str, Any]:
        compression_ratio = 0.5 if self.target_precision == "INT8" else 0.25
        quantized_size = original_size_mb * compression_ratio
        
        return {
            "original_size_mb": original_size_mb,
            "precision": self.target_precision,
            "quantized_size_mb": round(quantized_size, 2),
            "ram_savings_percent": f"{(1 - compression_ratio) * 100}%"
        }

if __name__ == "__main__":
    quantizer = ModelQuantizer("INT8")
    metrics = quantizer.quantize_weights( original_size_mb=14000.0) # 14GB FP16 model
    print("Quantization Metrics:", metrics)
