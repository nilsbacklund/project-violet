# Attack Labeller

In this folder currently lives the LogPrecis classifier.

A PyTorch-based tool to classify and label shell commands in long command-line sessions using a transformer model.

## Features

- Splits shell sessions into individual commands.
- Uses a token classification model to label each token and aggregate to
achieve labelling of commands.
- Supports long inputs via token-based chunking with overlap.
- Aggregates token-level predictions into command-level results.
- Outputs per-command labels and label spans.

