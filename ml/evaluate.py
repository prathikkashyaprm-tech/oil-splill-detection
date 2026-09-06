"""
MarineGuard AI - ML Model Evaluation & Benchmarking Suite
Computes Jaccard IoU, Dice/F1 Score, Pixel Precision, Recall, and Look-alike False Positive Rate.
"""

import os
import sys
import json
import glob
import numpy as np

# Add project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import torch
from ml.models.unet import SARUNet
from ml.dataset.noaa_loader import NOAAOilSpillDataset, generate_noaa_benchmark_dataset


def evaluate_model(model_path="models/unet_sar_oilspill.pth", data_dir="data/sar", output_report="ml/evaluation_report.json"):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[+] Running Evaluation on {device} using {model_path}...")

    # Ensure data exists
    images_dir = os.path.join(data_dir, "images")
    if not os.path.exists(images_dir) or len(glob.glob(os.path.join(images_dir, "*.png"))) == 0:
        generate_noaa_benchmark_dataset(data_dir, num_samples=30)

    image_paths = sorted(glob.glob(os.path.join(data_dir, "images", "*.png")))
    mask_paths = [p.replace("images", "masks").replace(".png", "_mask.png") for p in image_paths]

    dataset = NOAAOilSpillDataset(image_paths, mask_paths)
    loader = torch.utils.data.DataLoader(dataset, batch_size=4, shuffle=False)

    model = SARUNet(n_channels=3, n_classes=1, bilinear=True, use_attention=True).to(device)

    if os.path.exists(model_path):
        checkpoint = torch.load(model_path, map_location=device, weights_only=False)
        if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
            model.load_state_dict(checkpoint["model_state_dict"])
        else:
            model.load_state_dict(checkpoint)
        print(f"Loaded weights from {model_path}")
    else:
        print("[!] Model checkpoint not found, evaluating initialized model...")

    model.eval()

    total_tp = 0
    total_fp = 0
    total_fn = 0
    total_tn = 0
    sample_scores = []

    with torch.no_grad():
        for i, (imgs, masks) in enumerate(loader):
            imgs = imgs.to(device)
            masks = masks.to(device)
            outputs = model(imgs)
            preds = (torch.sigmoid(outputs) > 0.5).float()

            for b in range(imgs.size(0)):
                p = preds[b].cpu().numpy().flatten()
                m = masks[b].cpu().numpy().flatten()

                tp = int(np.sum((p == 1) & (m == 1)))
                fp = int(np.sum((p == 1) & (m == 0)))
                fn = int(np.sum((p == 0) & (m == 1)))
                tn = int(np.sum((p == 0) & (m == 0)))

                total_tp += tp
                total_fp += fp
                total_fn += fn
                total_tn += tn

                inter = tp
                union = tp + fp + fn
                iou = inter / (union + 1e-6)
                dice = (2.0 * inter) / (2.0 * inter + fp + fn + 1e-6)

                sample_scores.append({
                    "sample_idx": i * loader.batch_size + b,
                    "image": os.path.basename(image_paths[min(i * loader.batch_size + b, len(image_paths)-1)]),
                    "iou": float(iou),
                    "dice": float(dice),
                    "tp": tp,
                    "fp": fp,
                    "fn": fn
                })

    global_precision = total_tp / (total_tp + total_fp + 1e-6)
    global_recall = total_tp / (total_tp + total_fn + 1e-6)
    global_dice = (2.0 * total_tp) / (2.0 * total_tp + total_fp + total_fn + 1e-6)
    global_iou = total_tp / (total_tp + total_fp + total_fn + 1e-6)
    accuracy = (total_tp + total_tn) / (total_tp + total_fp + total_fn + total_tn + 1e-6)

    report = {
        "model": "MarineGuard Attention U-Net",
        "benchmark_dataset": "NOAA NESDIS / Sentinel-1 SAR Oil Spill Benchmark",
        "total_test_samples": len(dataset),
        "metrics": {
            "mean_iou_jaccard": round(float(global_iou), 4),
            "mean_dice_f1": round(float(global_dice), 4),
            "pixel_precision": round(float(global_precision), 4),
            "pixel_recall": round(float(global_recall), 4),
            "overall_accuracy": round(float(accuracy), 4),
            "lookalike_false_positive_rate": round(float(total_fp / (total_fp + total_tn + 1e-6)), 5)
        },
        "confusion_matrix": {
            "true_positive_pixels": total_tp,
            "false_positive_pixels": total_fp,
            "false_negative_pixels": total_fn,
            "true_negative_pixels": total_tn
        },
        "sample_evaluations": sample_scores[:10]
    }

    os.makedirs(os.path.dirname(output_report), exist_ok=True)
    with open(output_report, "w") as f:
        json.dump(report, f, indent=2)

    print("\n" + "="*50)
    print("[*] MARINEGUARD AI - MODEL BENCHMARK RESULTS")
    print("="*50)
    print(f"Jaccard Index (IoU)  : {report['metrics']['mean_iou_jaccard'] * 100:.2f}%")
    print(f"Dice Coefficient (F1): {report['metrics']['mean_dice_f1'] * 100:.2f}%")
    print(f"Precision            : {report['metrics']['pixel_precision'] * 100:.2f}%")
    print(f"Recall               : {report['metrics']['pixel_recall'] * 100:.2f}%")
    print(f"Overall Accuracy     : {report['metrics']['overall_accuracy'] * 100:.2f}%")
    print(f"Look-alike FPR       : {report['metrics']['lookalike_false_positive_rate'] * 100:.3f}%")
    print("="*50)
    print(f"Report saved to {output_report}\n")

    return report


if __name__ == "__main__":
    evaluate_model()
