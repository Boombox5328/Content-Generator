// Where each era's milestone sits along the road (road runs along -z at x=0).
export const ROAD_LEN = 1750;
export const SITES = {
  hometownA: { x: -30, z: -30,   r: 120 },
  b3: { x: 0,   z: -190,  r: 85 },
  b4: { x: 135, z: -380,  r: 150 },   // US map sits beside the road
  b5: { x: 0,   z: -600,  r: 110 },
  b6: { x: 0,   z: -830,  r: 110 },
  b7: { x: 0,   z: -1020, r: 90 },
  b8: { x: 0,   z: -1200, r: 90 },
  b9: { x: 0,   z: -1500, r: 60 },
  hometownB: { x: -30, z: -30 - ROAD_LEN, r: 120 },
};
