# Colab CUDA/cuGraph routing benchmark receipt

## Environment

- Platform: Linux 6.6.122 x86_64 (Google Colab)
- GPU: NVIDIA Tesla T4, 15,360 MiB
- Driver / CUDA reported by `nvidia-smi`: 580.82.07 / 13.0
- PyTorch: 2.11.0+cu128; CUDA available
- cuGraph: 26.02.00
- Repository revision for the completed GPU run: `1ca7ff5`

## Comparable workload

Both runs use `configs/v1_atlanta_tract_study.yaml` after rebuilding the
public inputs in the Colab runtime: 22,145 graph nodes, 56,516 directed input
edges, 50 origins, 101 destinations, and 5,050 OD pairs.

| Measure | CPU | GPU |
| --- | ---: | ---: |
| Routing time | 13.7883 s | 9.5820 s |
| GPU graph setup | — | 0.5418 s |
| End-to-end GPU setup + routing | — | 10.1238 s |
| Reachable OD pairs | not emitted by the CPU receipt | 4,700 / 5,050 |

The routing-only comparison is 1.44x in favor of the GPU; including graph
construction it is 1.36x. This is a single-run engineering benchmark, not a
claim about production throughput. The CPU and GPU JSON outputs were displayed
in the user-operated ephemeral Colab runtime; preserve the raw JSON receipts
alongside this summary when exporting the study evidence.
