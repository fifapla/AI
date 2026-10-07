from typing import List, Dict, Any

class FineTuningMonitor:
    def __init__(self, loss_threshold: float = 0.05):
        self.loss_threshold = loss_threshold

    def evaluate_epoch_logs(self, history: List[Dict[str, float]]) -> Dict[str, Any]:
        if len(history) < 2:
            return {"status": "INSUFFICIENT_DATA"}

        last_loss = history[-1]["val_loss"]
        prev_loss = history[-2]["val_loss"]
        
        overfitting_detected = (last_loss - prev_loss) > self.loss_threshold
        
        return {
            "current_epoch": len(history),
            "latest_val_loss": last_loss,
            "overfitting_risk": overfitting_detected,
            "action_recommended": "EARLY_STOPPING" if overfitting_detected else "CONTINUE_TRAINING"
        }

if __name__ == "__main__":
    monitor = FineTuningMonitor()
    training_logs = [
        {"epoch": 1, "train_loss": 2.4, "val_loss": 2.5},
        {"epoch": 2, "train_loss": 1.8, "val_loss": 1.9},
        {"epoch": 3, "train_loss": 1.1, "val_loss": 2.1}  # Validation loss increased
    ]
    report = monitor.evaluate_epoch_logs(training_logs)
    print("Fine-Tuning Health Report:", report)
