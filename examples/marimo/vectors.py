import marimo

__generated_with = "0.13.11"
app = marimo.App()


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # Vectors and Linear Algebra

    A *vector* is an ordered array of numbers (`list`) where each number has an assigned place.

    Vectors are used to represent points in vector space.

    Vectors must only contain numerical, usually floats.

    Vectors in the same space must have the same number of dimensions.
    """
    )
    return


@app.cell
def _():
    import numpy as np
    return (np,)


@app.cell
def _(np):
    np.array(range(4))
    return


@app.cell
def _(np):
    x = np.array(range(4))
    x
    return (x,)


@app.cell
def _(x):
    x[3] = 4
    return


@app.cell
def _(x):
    x
    return


@app.cell
def _(x):
    x * 2
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## Vector length and normalization

    length is also called *norm*

    square each and take the root of the sum
    """
    )
    return


@app.cell
def _(np):
    x_1 = np.array([3, 4])
    return (x_1,)


@app.cell
def _(np, x_1):
    np.linalg.norm(x_1)
    return


@app.cell
def _(x_1):
    y = x_1 * 2
    return (y,)


@app.cell
def _(y):
    y
    return


@app.cell
def _(np, y):
    np.linalg.norm(y)
    return


@app.cell
def _(np, x_1):
    x_normalized = x_1 / np.linalg.norm(x_1)
    return (x_normalized,)


@app.cell
def _(x_normalized):
    x_normalized
    return


@app.cell
def _(np, x_normalized):
    np.linalg.norm(x_normalized)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""Normalization scales the vector so all its dimensions are less than 1. Makes it easier to compute cosine distance between to vectors.""")
    return


@app.cell
def _():
    import marimo as mo
    return (mo,)


if __name__ == "__main__":
    app.run()
