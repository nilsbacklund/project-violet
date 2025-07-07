import re

def divide_statements(session, add_special_token, special_token="[STAT]"):
    """Divide a session into statements.
    This function splits a session into statements using specified separators. Optionally,
    it adds a special token at the beginning of each statement.
    Args:
        session (str): The session to be divided into statements.
        add_special_token (bool): Whether to add a special token to each statement.
        special_token (str, optional): The special token to be added. Defaults to "[STAT]".
    Returns:
        list of str: A list of statements.
    """
    statements = re.split(r"(; |\|\|? |&& )", session + " ")
    # concatenate with separators
    if len(statements) != 1:
        statements = [
            "".join(statements[i : i + 2]).strip()
            for i in range(0, len(statements) - 1, 2)
        ]
    else:  # cases in which there is only 1 statement > must end with " ;"
        statements = [statements[0].strip() + " ;"]
    if add_special_token:
        # Add separator
        statements = [f"{special_token} " + el for el in statements]
    return statements


def assign_labels2tokens(labels, statements):
    """Assign labels to tokens based on statements.
    This function assigns labels to tokens based on the provided labels and statements.
    Args:
        labels (str): The labels separated by '--'.
        statements (list of str): The statements to assign labels to.
    Returns:
        list of str: A list of labels assigned to tokens.
    """
    labels = labels.split(" -- ")
    tokens_labels = list()
    for label, statement in zip(labels, statements):
        for word in statement.split(" "):
            if word != "[STAT]":
                tokens_labels.append(label)
    return tokens_labels


def word_truncation(session, max_length):
    """Truncate words in a session to a maximum length.
    This function truncates words in a session to a maximum length specified.
    Args:
        session (str): The session to truncate words in.
        max_length (int): The maximum length allowed for each word.
    Returns:
        str: The session with truncated words.
    """
    return " ".join(
        map(
            lambda word: word[:max_length] if len(word) > max_length else word,
            session.split(" "),
        )
    )


def expand_labels(labels):
    """Expand abbreviated labels to statement labels.
    This function expands abbreviated labels to 1 label per statement based on the provided input.
    Args:
        labels (str): The labels separated by '--' with index information.
    Returns:
        list of str: A list of expanded labels.
    """
    labels = labels.split(" -- ")
    statement_labels = []
    prev_index = 0
    for label in labels:
        label, index = label.split(" - ")
        index = int(index)
        for _ in range(index - prev_index + 1):
            statement_labels.append(label.strip())
        prev_index = index + 1
    return statement_labels