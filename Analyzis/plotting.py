import matplotlib.pyplot as plt


def plot_positions_3d(
    positions: NDArray[np.float64], box_length_reduced: float
) -> None:
    """Display particle positions in a cubic periodic box."""

    figure = plt.figure()
    axes = figure.add_subplot(111, projection="3d")
    axes.scatter(positions[:, 0], positions[:, 1], positions[:, 2], s=10)
    axes.set(
        xlim=(0, box_length_reduced),
        ylim=(0, box_length_reduced),
        zlim=(0, box_length_reduced),
        xlabel="x (reduced units)",
        ylabel="y (reduced units)",
        zlabel="z (reduced units)",
    )
    axes.set_box_aspect((1, 1, 1))
    plt.show()
