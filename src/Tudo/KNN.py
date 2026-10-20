import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial.distance import euclidean
from sklearn.decomposition import PCA
from random import random

# --------------------------
# Example n-dimensional data
# --------------------------
n_dims = 8
dataset = [[random() for _ in range(n_dims)] for _ in range(50)]
testsample = [random() for _ in range(n_dims)]
k = 10

# --------------------------
# Dimensionality reduction (PCA)
# --------------------------
all_points = np.array(dataset + [testsample])
pca = PCA(n_components=2)
points_2d = pca.fit_transform(all_points)

dataset_2d = points_2d[:-1]
testsample_2d = points_2d[-1]

# --------------------------
# KNN in 2D PCA space
# --------------------------
def getKNN(k, testSample, dataset):
    distances = [(dp, float(euclidean(testSample, dp))) for dp in dataset]
    distances.sort(key=lambda e: e[1])
    knns = [d[0] for d in distances[:k]]
    return knns

# KNN in PCA space
knns_pca_2d = getKNN(k, testsample_2d, dataset_2d)

# --------------------------
# KNN in original 8D space
# --------------------------
knns_orig_8d = getKNN(k, testsample, dataset)

# Project original 8D KNN points to the same PCA 2D space
knns_orig_2d = pca.transform(np.array(knns_orig_8d))

# --------------------------
# Plot everything
# --------------------------
x_group, y_group = zip(*dataset_2d)
x_knns_pca, y_knns_pca = zip(*knns_pca_2d)
x_knns_orig, y_knns_orig = zip(*knns_orig_2d)
x_special, y_special = testsample_2d

plt.figure(figsize=(9,7))
plt.scatter(x_group, y_group, color='blue', s=30, alpha=0.5, label='dataset')
plt.scatter(x_knns_pca, y_knns_pca, color='red', s=60, label='KNN in PCA space')
plt.scatter(x_knns_orig, y_knns_orig, color='orange', s=60, marker='x', label='KNN in original 8D')
plt.scatter(x_special, y_special, color='green', s=120, label='test sample')
plt.legend()
plt.xlabel('PCA component 1')
plt.ylabel('PCA component 2')
plt.title('Compare KNN in PCA space vs original 8D space')
plt.show()