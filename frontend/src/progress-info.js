class CompletedAtom {

}

/**
 * This represents some indeterminate progress
 * for a long-running operation.
 */
class ProgressAtom {

  /**
   * Creates a
   * @param {int} text Human-readale description.
   */
  constructor(text) {
    this.text = text;
  }

}

/** Indicates that something went wrong, no more stages are attempted. */
class FailureAtom extends ProgressAtom {
}

/**
 * This class represents some determinate progress.
 */
class StructuredProgressAtom extends ProgressAtom {
  /**
   * Creates a StructuredProgressAtom, which tries to give some feedback about a long-running process.
   * @param text The human-readable description of the task.
   * @param stage The current step (e.g. 1 out of 7 tasks.)
   * @param total The total number of tasks.
   */
  constructor(text, stage, total) {
    super(text);
    this.stage = stage;
    this.total = total;
  }
}
