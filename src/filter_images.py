import pathlib
import os
import math

from PIL import Image
import imagehash
import cv2 as cv
import numpy as np


def get_images(directory):
    img_files = pathlib.Path(directory).iterdir()
    imgs = [
        p for p in map(str, img_files)
        if p.endswith('.jpg') or p.endswith('.png')
    ]
    imgs.sort()
    return imgs


def flip(h, i):
    bits = h.hash.flatten().copy()
    bits[i] = not bits[i]
    return imagehash.ImageHash(bits)


def hash_compare(directory, dups_dir, flip_hash=False):
    hash_bucket = {}
    for img_path in get_images(directory):
        h = imagehash.average_hash(Image.open(img_path))
        if h in hash_bucket:
            print(f'{hash_bucket[h]} and {img_path} are similar (same hash)')
            os.rename(img_path,
                      os.path.join(dups_dir, os.path.basename(img_path)))
        else:
            hash_bucket[h] = img_path

    if flip_hash:
        for h in list(hash_bucket):
            for i in range(len(h)):
                h2 = flip(h, i)
                if h2 in hash_bucket and os.path.exists(hash_bucket[h2]):
                    print(
                        f'{hash_bucket[h]} and {hash_bucket[h2]} are similar' +
                        ' (Hamming distance 1)')
                    os.rename(
                        hash_bucket[h2],
                        os.path.join(dups_dir,
                                     os.path.basename(hash_bucket[h2])))
            hash_bucket.pop(h)


def filter_blurred(directory, blurred_dir, threshold=5, size=60):
    for img_path in get_images(directory):
        im = cv.imread(img_path, 0)
        h, w = im.shape
        centerY, centerX = h // 2, w // 2
        fft = np.fft.fft2(im)
        fft_shift = np.fft.fftshift(fft)
        fft_shift[centerY - size:centerY + size,
                  centerX - size:centerX + size] = 0
        fft_shift = np.fft.ifftshift(fft_shift)
        recon = np.fft.ifft2(fft_shift)
        magnitude = 20 * np.log(np.abs(recon))
        mean = np.mean(magnitude)

        if mean <= threshold:
            print(f'{img_path} is blurry ({mean:.02f})')
            os.rename(img_path,
                      os.path.join(blurred_dir, os.path.basename(img_path)))


def entropy(im):
    hist, _ = np.histogram(im, bins=range(256), density=True)
    hist = hist[hist.nonzero()]
    entropy = -(hist * np.log(hist) / np.log(math.e)).sum()
    return entropy


def filter_outliers(directory, outliers_dir):
    imgs = get_images(directory)
    imgs_metric = []
    for img_path in imgs:
        im = cv.imread(img_path, 0)
        imgs_metric.append(entropy(im))

    outliers = []
    lower_quantile = np.percentile(imgs_metric, 25)
    upper_quantile = np.percentile(imgs_metric, 75)
    iqr_constant = 1.5
    iqr = (upper_quantile - lower_quantile) * iqr_constant
    quantile_range = (lower_quantile - iqr, upper_quantile + iqr)
    for img_path, metric in zip(imgs, imgs_metric):
        if metric < quantile_range[0] or metric > quantile_range[1]:
            outliers.append((img_path, metric))

    for outlier, metric in outliers:
        print(f'{outlier} is lighter or darker than others ({metric:.02f})')
        os.rename(outlier, os.path.join(outliers_dir,
                                        os.path.basename(outlier)))


def filter_low_contrast(directory, low_contrast_dir, threshold=2):
    for img_path in get_images(directory):
        im = cv.imread(img_path, 0)
        h, w = im.shape
        cropped = im[round(h * 0.1):round(h * 0.9),
                     round(w * 0.1):round(w * 0.9)]
        metric = entropy(cropped)
        if metric < threshold:
            print(f'{img_path} has low contrast ({metric:.02f})')
            os.rename(
                img_path,
                os.path.join(low_contrast_dir, os.path.basename(img_path)))


if __name__ == '__main__':
    directory = 'images/undefined/'

    dups_dir = os.path.join(directory, 'copies')
    if not os.path.exists(dups_dir):
        os.makedirs(dups_dir)

    low_contrast_dir = os.path.join(directory, 'low_contrast')
    if not os.path.exists(low_contrast_dir):
        os.makedirs(low_contrast_dir)

    filter_low_contrast(directory, low_contrast_dir)
    hash_compare(directory, dups_dir)
