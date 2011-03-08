import collada
import sys
import traceback

print 'Attempting to load file %s' % sys.argv[1]

try:
    col = collada.Collada(sys.argv[1], \
            ignore=[collada.DaeUnsupportedError, collada.DaeBrokenRefError])
except:
    traceback.print_exc()
    print
    print "Failed to load collada file."
    sys.exit(1)

print
print 'Successfully loaded collada file.'
print 'There were %d errors' % len(col.errors)

for e in col.errors:
    print e
