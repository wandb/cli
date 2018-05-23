import _ from 'lodash';

export function makeHistogram(valuesOrHistogram, numBuckets, min, max) {
  if (Array.isArray(valuesOrHistogram)) {
    return makeHistogramFromValues(valuesOrHistogram, numBuckets, min, max);
  } else if (valuesOrHistogram._type == 'histogram') {
    return makeHistogramFromHistogram(valuesOrHistogram, numBuckets, min, max);
  }
}

export function makeHistogramFromHistogram(
  histogram,
  numBuckets = 10,
  min = null,
  max = null
) {
  let values = sampleHistogram(histogram);
  return makeHistogramFromValues(values, numBuckets, min, max);
}

export function makeHistogramFromValues(
  values,
  numBuckets = 10,
  min = null,
  max = null
) {
  /**
   * builds a histogram of values for evenly spaced buckets from max to min.
   * * If max and min unspecified, set to max and min of values.
   */

  if (min == null) {
    min = _.min(values);
  }
  if (max == null) {
    max = _.max(values);
  }

  if (min == max) {
    binEdges = [min, min + 1];
    counts = [values.length];
    return {counts: counts, binEdges: binEdges};
  }

  let binEdges = [];
  let bucketWidth = (max - min) / numBuckets;

  let counts = Array(numBuckets)
    .fill()
    .map(e => 0);

  for (let i = 0; i < numBuckets + 1; i++) {
    binEdges.push(min + i * bucketWidth);
  }

  values.map(v => {
    let bucket = Math.floor((v - min) / bucketWidth);
    if (bucket >= numBuckets) {
      bucket = numBuckets - 1;
    } else if (bucket < 0) {
      bucket = 0;
    }
    counts[bucket]++;
  });
  return {counts: counts, binEdges: binEdges};
}

export function sampleHistogram(histogram) {
  /* Takes in a wandb histogram object and returns an array of points */
  if (!histogram._type) {
    console.log('Warning: passed in an unknown type to sampleHistogram');
  }
  if (!histogram._type == 'histogram') {
    console.log(
      'Warning: passed in an object that does not have histogram type to sampleHistogram'
    );
  }
  if (!histogram.bins) {
    console.log('Warning: missing bins');
  }
  if (!histogram.values) {
    console.log('Warning: missing values');
  }

  let retArr = [];
  for (let i = 1; i < histogram.bins.length; i++) {
    let left = histogram.bins[i - 1];
    let right = histogram.bins[i];
    for (let j = 0; j < histogram.values[i - 1]; j++) {
      retArr.push(_.random(left, right));
    }
  }

  return retArr;
}
