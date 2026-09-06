"""
MarineGuard AI - U-Net SAR Oil Spill Training Pipeline
Trains U-Net on NOAA NESDIS & Sentinel-1 SAR imagery with Dice + BCE Loss.
"""

import os
import sys
import glob
import time
import argparse
import numpy as np

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import torch
import torch.optim as optim
from torch.utils.data import DataLoader, random_split

from ml.models.unet import SARUNet, DiceBCELoss
from ml.dataset.noaa_loader import NOAAOilSpillDataset, generate_noaa_benchmark_dataset


def train_unet(data_dir="data/sar", epochs=10, batch_size=8, lr=1e-3, device=None, save_path="models/unet_sar_oilspill.pth"):
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[+] Training MarineGuard SAR U-Net on {device}...")

    # Ensure dataset exists
    images_dir = os.path.join(data_dir, "images")
    if not os.path.exists(images_dir) or len(glob.glob(os.path.join(images_dir, "*.png"))) == 0:
        print(f"Synthesizing NOAA benchmark SAR dataset in {data_dir}...")
        generate_noaa_benchmark_dataset(data_dir, num_samples=60)

    image_paths = sorted(glob.glob(os.path.join(data_dir, "images", "*.png")))
    mask_paths = [p.replace("images", "masks").replace(".png", "_mask.png") for p in image_paths]

    dataset = NOAAOilSpillDataset(image_paths, mask_paths)
    val_size = max(2, int(0.2 * len(dataset)))
    train_size = len(dataset) - val_size
    train_set, val_set = random_split(dataset, [train_size, val_size])

    train_loader = DataLoader(train_set, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_set, batch_size=batch_size, shuffle=False)

    model = SARUNet(n_channels=3, n_classes=1, bilinear=True, use_attention=True).to(device)
    criterion = DiceBCELoss()
    optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=2)

    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    best_loss = float("inf")

    history = {"train_loss": [], "val_loss": [], "val_dice": [], "val_iou": []}

    for epoch in range(1, epochs + 1):
        model.train()
        train_loss = 0.0
        start_time = time.time()

        for imgs, masks in train_loader:
            imgs, masks = imgs.to(device), masks.to(device)
            optimizer.zero_grad()
            outputs = model(imgs)
            loss = criterion(outputs, masks)
            loss.backward()
            optimizer.step()
            train_loss += loss.item() * imgs.size(0)

        train_loss /= len(train_set)

        # Validation
        model.eval()
        val_loss = 0.0
        dice_total = 0.0
        iou_total = 0.0

        with torch.no_grad():
            for imgs, masks in val_loader:
                imgs, masks = imgs.to(device), masks.to(device)
                outputs = model(imgs)
                loss = criterion(outputs, masks)
                val_loss += loss.item() * imgs.size(0)

                preds = (torch.sigmoid(outputs) > 0.5).float()
                inter = (preds * masks).sum().item()
                union = preds.sum().item() + masks.sum().item()
                
                dice = (2.0 * inter + 1e-6) / (union + 1e-6)
                iou = (inter + 1e-6) / (union - inter + 1e-6)
                dice_total += dice * imgs.size(0)
                iou_total += iou * imgs.size(0)

        val_loss /= len(val_set)
        val_dice = dice_total / len(val_set)
        val_iou = iou_total / len(val_set)
        scheduler.step(val_loss)

        history["train_loss"].append(train_loss)
        history["val_loss"].append(val_loss)
        history["val_dice"].append(val_dice)
        history["val_iou"].append(val_iou)

        elapsed = time.time() - start_time
        print(f"Epoch [{epoch:02d}/{epochs:02d}] ({elapsed:.1f}s) - Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f} | Dice: {val_dice:.4f} | IoU: {val_iou:.4f}")

        if val_loss < best_loss:
            best_loss = val_loss
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "val_dice": val_dice,
                "val_iou": val_iou
            }, save_path)
            print(f"  [+] Checkpoint saved to {save_path} (Best Val Loss: {best_loss:.4f})")

    print(f"[+] Training Complete! Model saved at {save_path}")
    return model, history


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train SAR U-Net for MarineGuard AI")
    parser.add_argument("--epochs", type=int, default=10, help="Number of epochs")
    parser.add_argument("--batch-size", type=int, default=8, help="Batch size")
    parser.add_argument("--lr", type=float, default=1e-3, help="Learning rate")
    parser.add_argument("--data", type=str, default="data/sar", help="Path to SAR data")
    parser.add_argument("--save", type=str, default="models/unet_sar_oilspill.pth", help="Model destination")
    args = parser.parse_args()

    train_unet(data_dir=args.data, epochs=args.epochs, batch_size=args.batch_size, lr=args.lr, save_path=args.save)
