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
    import marimo as mo
    return (mo,)


if __name__ == "__main__":
    app.run()
