import uuid

import coiled.v2
import dask
from distributed import Client, wait


def test_repeated_merge_spill():
    # See https://github.com/dask/distributed/issues/6110

    with coiled.v2.Cluster(
        name=f"test_deadlock-{uuid.uuid4().hex}",
        n_workers=20,
        worker_vm_types=["t3.medium"],
    ) as cluster:
        with Client(cluster) as client:
            ddf = dask.datasets.timeseries(
                "2020",
                "2025",
                partition_freq="2w",
            )
            ddf2 = dask.datasets.timeseries(
                "2020",
                "2023",
                partition_freq="2w",
            )

            i = 1
            for i in range(4):
                client.restart()
                fs = client.compute((ddf.x + ddf.y).mean())
                wait(fs, timeout=2 * 60)
                del fs

                ddf3 = ddf.merge(ddf2)
                fs = client.compute((ddf3.x + ddf3.y).mean())
                wait(fs, timeout=2 * 60)
                del fs
                i += 1
