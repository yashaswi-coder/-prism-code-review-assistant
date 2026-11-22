import pickle


def load_data(path: str):
    with open(path, "rb") as source:
        return pickle.load(source)
