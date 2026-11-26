import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "kit"))

import dfkit as k

OUT = os.environ.get("OUT", "/tmp/dfkit")

k.reset()
crate = k.finish("df_crate", k.crate("crate", (1.1, 0.8, 0.75)), budget=800)
print("STATS", k.stats(crate))
k.export(crate, os.path.join(OUT, "df_crate.glb"))
print("SHEET", k.preview([crate], os.path.join(OUT, "df_crate_sheet.png")))

k.reset()
drum = k.finish("df_drum", k.barrel("drum", 0.3, 0.88), budget=600)
print("STATS", k.stats(drum))
k.export(drum, os.path.join(OUT, "df_drum.glb"))
print("SHEET", k.preview([drum], os.path.join(OUT, "df_drum_sheet.png")))
