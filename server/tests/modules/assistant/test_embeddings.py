from app.modules.assistant.embeddings import hash_embed

QUESTION = "夏天怎么给狗降温"
STOCK = "今天上证指数多少"
PASSAGE = (
    "夏天给狗降温\n"
    "夏天给狗降温，先避开正午出门，改在清晨或傍晚。屋里通风、留阴凉处，随时有干净凉水。"
    "可以用湿毛巾擦肚皮和脚垫散热，不要浇冰水、不要把狗关在停驶的车里。"
    "我是小x，这是说明书里的日常护理，不能代替兽医。"
)


def cosine(left: list[float], right: list[float]) -> float:
    return sum(x * y for x, y in zip(left, right))


def test_same_text_same_unit_vector() -> None:
    first = hash_embed("夏天怎么给狗降温", 1024)
    second = hash_embed("夏天怎么给狗降温", 1024)

    assert first == second
    assert abs(sum(value * value for value in first) - 1) < 1e-6


def test_cooling_passage_beats_unrelated_question() -> None:
    question = hash_embed(QUESTION, 1024)
    passage = hash_embed(PASSAGE, 1024)
    stock = hash_embed(STOCK, 1024)

    assert cosine(question, passage) > 0.25
    assert cosine(question, passage) > cosine(question, stock)
