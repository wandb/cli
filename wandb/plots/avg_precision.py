import wandb
from wandb import util
from wandb.plots.utils import test_missing, test_types, encode_labels
chart_limit = wandb.Table.MAX_ROWS

def avg_precision(y_true=None, y_probas=None):
    """
    Computes the tradeoff between precision and recall for different thresholds.
        A high area under the curve represents both high recall and high precision,
        where high precision relates to a low false positive rate, and high recall
        relates to a low false negative rate. High scores for both show that the
        classifier is returning accurate results (high precision), as well as
        returning a majority of all positive results (high recall).
        PR curve is useful when the classes are very imbalanced.

    Arguments:
    y_true (arr): Test set labels.
    y_probas (arr): Test set predicted probabilities.
    labels (list): Named labels for target varible (y). Makes plots easier to
      read by replacing target values with corresponding index.
      For example labels= ['dog', 'cat', 'owl'] all 0s are
      replaced by 'dog', 1s by 'cat'.

    Returns:
    Nothing. To see plots, go to your W&B run page then expand the 'media' tab
    under 'auto visualizations'.

    Example:
    wandb.log({'pr': wandb.plots.precision_recall(y_true, y_probas, labels)})
    """
    np = util.get_module("numpy", required="roc requires the numpy library, install with `pip install numpy`")
    scikit = util.get_module("sklearn", "roc requires the scikit library, install with `pip install scikit-learn`")

    y_true = np.array(y_true)
    y_probas = np.array(y_probas)

    if (test_missing(y_true=y_true, y_probas=y_probas) and
        test_types(y_true=y_true, y_probas=y_probas)):
        classes = np.unique(y_true)
        probas = y_probas

        binarized_y_true = scikit.preprocessing.label_binarize(y_true, classes=classes)
        precision_micro_avg, recall_micro_avg, _ = scikit.metrics.precision_recall_curve(binarized_y_true.ravel(),
                                                 y_probas.ravel())
        data=[]
        for p_m, r_m in zip(precision_micro_avg, recall_micro_avg):
            data.append([r_m, p_m])
        # TODO: what is an optimal subsampling rate?
        subsample_every_n = 50
        data_full = np.asarray(data, dtype=np.float32)
        data_subsamples = data_full[0::subsample_every_n].tolist()
        table = wandb.Table(data=data, columns=["recall_micro_avg", "precision_micro_avg"])
        fields = {"fieldSettings" : {"run_name" : "name", "recall" : "recall_micro_avg", "precision" : "precision_micro_avg"}}
        return wandb.log({
                'avg_precision' : wandb.run.plot_table("builtin:avg-precision", "avg_precison", table,  fields)})
