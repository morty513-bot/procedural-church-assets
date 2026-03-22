# v15 immediate fix
- Fixed central stack to remove gaps using world-space min/max Z contact constraints.
- Overlap epsilon: 0.015 m
- Rendered wider camera framing to show full spire.

## Central stack after fix (minZ -> maxZ)
- Cube: 0.0000 -> 6.4000
- Cylinder: 6.3850 -> 8.5850
- Cone: 9.3000 -> 10.6000
- Cone.001: 10.4500 -> 15.4500
- Cylinder.001: 15.4300 -> 15.7100
- Sphere: 15.6900 -> 15.9500
- Cube.005: 15.9300 -> 16.1550
- Cube.006: 16.1350 -> 16.1620
