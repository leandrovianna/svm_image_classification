import os

import cv2 as cv
import numpy as np

hog = cv.HOGDescriptor('models/hog_model.xml')
svm = cv.ml.SVM.load('models/svm_model.dat')

win_size = hog.winSize
cell_size = hog.cellSize

file_paths = []
features = []
while True:
    try:
        file_path = os.path.abspath(input())
        if file_path and not os.path.exists(file_path):
            print(f'File {file_path} do not exists.')
            continue
        im = cv.imread(file_path, cv.IMREAD_GRAYSCALE)
        if im is None:
            print(f'Opencv do not opened {file_path}. ' +
                  'Maybe it is not a image.')
            continue
        assert (im.shape[::-1] == win_size)
        features.append(hog.compute(im))
        file_paths.append(file_path)
    except EOFError:
        break

features = np.float32(features).reshape(-1, len(features[0]))
result = svm.predict(features)[1]

visual = True

if visual:
    if not os.path.exists('results'):
        os.makedirs('results/')

print('Results:')
for file_path, label in zip(file_paths, result):
    is_positive = label[0] == 1
    print(f'{file_path}'.ljust(70) + f'{is_positive}'.rjust(10))

    if visual:
        im = cv.imread(file_path)
        cv.putText(im, 'POSITIVE' if is_positive else 'NEGATIVE', (100, 100),
                   cv.FONT_HERSHEY_SIMPLEX, 2,
                   (0, 255, 0, 255) if is_positive else (0, 0, 255, 255), 3)
        for x in range(cell_size[0], win_size[0], cell_size[0]):
            cv.line(im, (x, 0), (x, win_size[1] - 1), (0, 0, 0, 0), 4)
            cv.line(im, (x, 0), (x, win_size[1] - 1), (0, 255, 255, 0), 2)
        for y in range(cell_size[1], win_size[1], cell_size[1]):
            cv.line(im, (0, y), (win_size[0] - 1, y), (0, 0, 0, 0), 4)
            cv.line(im, (0, y), (win_size[0] - 1, y), (0, 255, 255, 0), 2)
        cv.imwrite(f'results/{os.path.basename(file_path)}', im)
