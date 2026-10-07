from typing import Dict, Any, List

class ModelDistiller:
    def __init__(self, teacher_model: str = "gpt-4o", student_model: str = "gpt-4o-mini"):
        self.teacher_model = teacher_model
        self.student_model = student_model

    def evaluate_distillation_gap(self, teacher_output: str, student_output: str) -> Dict[str, Any]:
        teacher_tokens = set(teacher_output.lower().split())
        student_tokens = set(student_output.lower().split())
        
        overlap = len(teacher_tokens.intersection(student_tokens)) / max(1, len(teacher_tokens))
        fidelity_score = round(overlap, 2)
        
        return {
            "teacher_model": self.teacher_model,
            "student_model": self.student_model,
            "fidelity_score": fidelity_score,
                        "status": "OPTIMAL_DISTILLATION" if fidelity_score >= 0.7 else "REQUIRES_FINE_TUNING"
        }

if __name__ == "__main__":
    distiller = ModelDistiller()
    teacher_res = "High-dimensional vector indexes optimize approximate nearest neighbor search efficiency."
    student_res = "Vector indexes optimize nearest neighbor search efficiency."
    
    report = distiller.evaluate_distillation_gap(teacher_res, student_res)
    print("Distillation Report:", report)
