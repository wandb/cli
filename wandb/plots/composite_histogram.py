import wandb
from wandb import util
from wandb.plots.utils import test_missing, test_types, encode_labels
chart_limit = wandb.Table.MAX_ROWS

def class_distributions(y_probas=None, labels=None, classes_to_plot=None):
    """
    Layer two histograms of class score distributions.

    Arguments:
    y_probas (arr): Test set predicted probabilities.
    labels (list): Named labels for target varible (y). Makes plots easier to
      read by replacing target values with corresponding index.
      For example labels= ['dog', 'cat', 'owl'] all 0s are
      replaced by 'dog', 1s by 'cat'.
    classes_to_plot (list): exactly two classes to compare in this histogram.
      Defaults to taking the first two classes.

    Returns:
    Nothing. To see plots, go to your W&B run page then expand the 'media' tab
    under 'auto visualizations'.

    Example:
    wandb.plots.class_distributions(y_probas, labels, classes_to_plot)
    """
    np = util.get_module("numpy", required="class_distributions requires the numpy library, install with `pip install numpy`")
    y_probas = np.array(y_probas)
    if test_missing(y_probas=y_probas):
        # default to plotting first two classes
        if classes_to_plot is None:
            classes_to_plot = [0, 1]
        elif len(classes_to_plot) != 2 or not isinstance(classes_to_plot, list):
            wandb.termwarn("class distribution plot requires a list of two classes")
            classes_to_plot = [0, 1]
        elif isinstance(classes_to_plot[0], str) and isinstance(classes_to_plot[1], str):
            if labels is None:
                wandb.termwarn("provide all label names to plots.class_distribution() or use class ids");
                classes_to_plot = [0, 1]
            else:
                c1 = labels.index(classes_to_plot[0])
                c2 = labels.index(classes_to_plot[1])
                classes_to_plot = [c1, c2]
        elif not isinstance(classes_to_plot[0], int) or not isinstance(classes_to_plot[1], int):
            wandb.termwarning("provide class distribution plot with classes label strings or class ids")
            classes_to_plot = [0, 1]
        
        # hopefully we covered it
        c1, c2 = classes_to_plot
        red_probas = y_probas[:, c1] #.transpose()
        blue_probas = y_probas[:, c2] #.transpose()
        # TODO: sample max here
        data = []
        for r, b in zip(red_probas, blue_probas):
		        data.append([r, b])

        table = wandb.Table(data=data, columns=["red_bins", "blue_bins"])
        fields = {"fieldSettings" : {"red_bins" : "red_bins", "blue_bins": "blue_bins"}}
        return wandb.log({
                'class_distribution' : wandb.run.plot_table("builtin:multi-histogram", "class_compare", table,  fields)})

def multi_histogram(red_bins, blue_bins):
    """
    Pass in to arrays of numbers
    """
    data = []
    #TODO: there must be a more efficient way?
    for r, b in zip(red_bins, blue_bins):
        data.append([r, b])
    table = wandb.Table(data=data, columns=["red_bins", "blue_bins"])
    fields = {"fieldSettings" : {"red_bins" : "red_bins", "blue_bins": "blue_bins"}}
    return wandb.log({
                'multi_histogram' : wandb.run.plot_table("builtin:multi-histogram", "multi_histogram", table,  fields)})



