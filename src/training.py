import pathlib
import random

import cv2 as cv
import numpy as np
from alive_progress import alive_bar

from params import win_size, cell_size, block_size, block_stride, n_bins, \
    feature_len


def hog_setup(win_size, cell_size, n_bins, block_size, block_stride):
    deriv_aperture = 1
    win_sigma = -1
    histogram_norm_type = 0
    l2_hys_threshold = 0.2
    gamma_correction = 1
    n_levels = 64
    signed_gradients = True

    hog = cv.HOGDescriptor(win_size, block_size, block_stride, cell_size,
                           n_bins, deriv_aperture, win_sigma,
                           histogram_norm_type, l2_hys_threshold,
                           gamma_correction, n_levels, signed_gradients)
    return hog


def preprocess(im, win_size):
    gray = cv.cvtColor(im, cv.COLOR_BGR2GRAY)
    gaussian = cv.GaussianBlur(gray, (21, 21), 0)
    _, thresh = cv.threshold(gaussian, 8, 255, cv.THRESH_BINARY)
    x, y, w, h = cv.boundingRect(thresh)
    cropped = im[y:y + h, x:x + w]
    if cropped.shape[0:2] == (0, 0):
        return None
    if cropped.shape[0:2][::-1] != win_size:
        cropped = cv.resize(cropped, win_size, cv.INTER_LINEAR)
    return cropped


def load_features(negatives_path, positives_path, hog):
    negatives_dir = pathlib.Path(negatives_path)
    positives_dir = pathlib.Path(positives_path)
    negatives_images = [
        name for name in map(str, negatives_dir.iterdir())
        if name.endswith('.jpg') or name.endswith('.png')
    ]
    positives_images = [
        name for name in map(str, positives_dir.iterdir())
        if name.endswith('.jpg') or name.endswith('.png')
    ]
    features_neg = []
    features_pos = []
    with alive_bar(len(negatives_images) + len(positives_images)) as bar:
        suffix = (f'.{win_size[0]}x{win_size[1]}#{block_size[0]}x' +
                  f'{block_size[1]}#{cell_size[0]}x{cell_size[1]}.npy')
        for img_path in negatives_images:
            data_path = pathlib.Path(f'{img_path}{suffix}')
            if data_path.is_file():
                features_neg.append(np.load(data_path))
            else:
                im = cv.imread(img_path)
                assert (im is not None)
                im = preprocess(im, win_size)
                if im is not None:
                    f = hog.compute(im)
                    np.save(data_path, f)
                    features_neg.append(f)
                else:
                    print(f'{img_path} ignored because is darker')
            bar()

        for img_path in positives_images:
            data_path = pathlib.Path(f'{img_path}{suffix}')
            if data_path.is_file():
                features_pos.append(np.load(data_path))
            else:
                im = cv.imread(img_path)
                assert (im is not None)
                im = preprocess(im, win_size)
                if im is not None:
                    f = hog.compute(im)
                    np.save(data_path, f)
                    features_pos.append(f)
                else:
                    print(f'{img_path} ignored because is darker')
            bar()

    return features_neg, features_pos


def separate_datasets(features_neg, features_pos):
    random.seed(0)
    random.shuffle(features_neg)
    random.shuffle(features_pos)

    percent_cut = 0.75
    train_neg_len = int(len(features_neg) * percent_cut)
    train_pos_len = int(len(features_pos) * percent_cut)
    train_data = []
    train_labels = []
    train_data.extend(f for f in features_neg[:train_neg_len])
    train_data.extend(f for f in features_pos[:train_pos_len])
    train_labels.extend(-1 for _ in range(train_neg_len))
    train_labels.extend(1 for _ in range(train_pos_len))
    assert (len(train_data) == len(train_labels))

    test_data = []
    test_labels = []
    test_data.extend(f for f in features_neg[train_neg_len:])
    test_data.extend(f for f in features_pos[train_pos_len:])
    test_labels.extend(-1 for _ in range(len(features_neg) - train_neg_len))
    test_labels.extend(1 for _ in range(len(features_pos) - train_pos_len))
    assert (len(test_data) == len(test_labels))

    return train_data, train_labels, test_data, test_labels


def summary_data(data, labels, title):
    count_neg = 0
    count_pos = 0
    for label in labels:
        if label == 1:
            count_pos += 1
        else:
            count_neg += 1

    print(f'{title} data:')
    print(f'{count_pos} positives examples.')
    print(f'{count_neg} negatives examples.')


def setup_svm(C=0.1, gamma=1):
    svm = cv.ml.SVM_create()
    svm.setType(cv.ml.SVM_C_SVC)
    svm.setC(C)
    svm.setKernel(cv.ml.SVM_RBF)
    svm.setGamma(gamma)
    return svm


def train():
    print('HOG Info:')
    print(f'Win Size: {win_size}')
    print(f'Cell Size: {cell_size}')
    print(f'Block Size: {block_size}')
    print(f'Block Stride: {block_stride}')
    print(f'Num. Bins {n_bins}')

    hog = hog_setup(win_size, cell_size, n_bins, block_size, block_stride)
    hog.save('models/hog_last_model.xml')

    features_neg, features_pos = load_features('images/negatives',
                                               'images/positives', hog)

    train_data, train_labels, test_data, test_labels = separate_datasets(
        features_neg, features_pos)

    summary_data(train_data, train_labels, 'Training')

    svm = setup_svm(C=1, gamma=1)

    train_data = np.float32(train_data).reshape(-1, feature_len)
    train_labels = np.int32(train_labels).reshape(-1, 1)
    with alive_bar(1) as bar:
        print('Begin training.')
        # svm.train(train_data, cv.ml.ROW_SAMPLE, train_labels)
        svm.trainAuto(train_data, cv.ml.ROW_SAMPLE, train_labels)
        print('Training complete.')
        model_path = 'models/svm_last_model.dat'
        print(f'Saving model at {model_path}')
        svm.save(model_path)
        bar()

    summary_data(test_data, test_labels, 'Test')

    test_data = np.float32(test_data).reshape(-1, feature_len)
    test_labels = np.int32(test_labels).reshape(-1, 1)
    result = svm.predict(test_data)[1]
    mask = result == test_labels
    correct = np.count_nonzero(mask)
    accuracy = correct * 100.0 / result.size
    print('Results:')
    print(f'Accurary: {accuracy:.2f}%')


if __name__ == '__main__':
    train()
