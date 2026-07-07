from anonymai import PIIType, ScrubStrategy, find_pii, scrub, unscrub

text = (
    "My name is Daniel and I'm from Jerusalem, I like to eat pizza. "
    "Daniel was my father's name as well."
)

entities = find_pii(text)
for entity in entities:
    print(entity)

result = scrub(text, strategy=ScrubStrategy.MOCK)
print(result.scrubbed_text)

restored = unscrub(result.scrubbed_text, result)
print(restored)
assert restored == text
