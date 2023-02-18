# Image Classification

Image Classification using Histogram of Gradients (HOG) and Support Vector 
Machines (SVM). This code is for learning purposes. Using HOG and SVM 
implementations from OpenCV.

## Tkinter interface to select images

```python
python src/select_images.py
```
GUI that show images at `images/undefined/` directory and moves to 
`images/positives/` or `images/negatives/`.

## Training SVM model

- Use `src/params.py` to define the parameters for the HOG descriptor.
- With the positive class images at `images/positives/` and the negative class
images at `images/negatives/`, run `python src/training.py` to train the model.

## Classification

- `src/classifier.py` run the classifier using `models/hog_model.xml` for the
HOG descriptor and `models/svm_model.dat` for SVM model.
- Input expected is a text file with an image file path on each line.
- If `visual` variable is `True`, the images will be saved on the directory
`results/` with a text indicating the classification result.

