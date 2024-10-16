import sys
import traceback

import collada

print(f"Attempting to load file {sys.argv[1]}")

try:
    col = collada.Collada(
        sys.argv[1], ignore=[collada.DaeUnsupportedError, collada.DaeBrokenRefError]
    )
except BaseException:
    traceback.print_exc()
    print()
    print("Failed to load collada file.")
    sys.exit(1)

print()
print("Successfully loaded collada file.")
print("There were %d errors" % len(col.errors))

for e in col.errors:
    print(e)
