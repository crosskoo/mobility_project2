#!/usr/bin/env python3
import sys
import os
import glob
import time

# ==============================================================================
# CARLA 모듈 경로 설정 (기존 코드와 동일)
# ==============================================================================
try:
    sys.path.append(glob.glob('../../../carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass

import carla
import rclpy
from rclpy.node import Node
import matplotlib.pyplot as plt

class SpawnPointViewer(Node):
    def __init__(self):
        super().__init__('spawn_point_viewer')
        
        # 1. CARLA 연결
        try:
            self.host = '127.0.0.1'
            self.port = 2000
            self.client = carla.Client(self.host, self.port)
            self.client.set_timeout(20.0) # 맵 로딩 시간을 고려해 타임아웃 늘림
            
            # 2. Town01 맵 로드 (현재 맵이 Town01이 아니면 로드)
            world = self.client.get_world()
            if "Town01" not in world.get_map().name:
                self.get_logger().info("Loading Town01 map... (Please wait)")
                self.client.load_world('Town01')
                # 맵 로딩 후 월드 객체 갱신
                world = self.client.get_world()
            
            self.world = world
            self.map = self.world.get_map()
            self.get_logger().info(f"Connected to CARLA. Current Map: {self.map.name}")

        except Exception as e:
            self.get_logger().error(f"Connection Failed: {e}")
            return

        # 3. 모든 스폰 포인트 가져오기
        self.spawn_points = self.map.get_spawn_points()
        self.get_logger().info(f"Found {len(self.spawn_points)} spawn points.")

        # 4. 시각화 실행
        self.plot_map_and_points()

    def plot_map_and_points(self):
        if os.environ.get('DISPLAY', '') == '':
            self.get_logger().warn("No display found. Cannot plot.")
            return

        self.get_logger().info("Plotting map and spawn points...")

        # (1) 지도(Topology) 데이터 준비
        topology = self.map.get_topology()
        ox, oy = [], []
        for wp1, wp2 in topology:
            l1, l2 = wp1.transform.location, wp2.transform.location
            ox.append(l1.x); oy.append(l1.y)
            ox.append(l2.x); oy.append(l2.y)
            ox.append(None); oy.append(None) # 선 끊기용

        # (2) 스폰 포인트 데이터 준비
        sx, sy = [], []
        for sp in self.spawn_points:
            sx.append(sp.location.x)
            sy.append(sp.location.y)

        # (3) Matplotlib 그리기
        plt.figure(figsize=(12, 12))
        
        # 도로망 그리기 (회색)
        plt.plot(ox, oy, "k-", linewidth=0.5, alpha=0.3, label="Roads")
        
        # 스폰 포인트 그리기 (파란 점)
        plt.scatter(sx, sy, c='blue', s=30, marker='o', alpha=0.6, label="Spawn Points")

        # ★ 포인트 옆에 인덱스 번호 텍스트 추가
        for i, (x, y) in enumerate(zip(sx, sy)):
            # 텍스트가 잘 보이도록 빨간색으로, 약간 옆에 표시
            plt.text(x, y, str(i), fontsize=9, color='red', fontweight='bold', clip_on=True)

        # 시작점(0번)은 별도로 크게 표시 (참고용)
        if len(sx) > 0:
            plt.plot(sx[0], sy[0], "g*", markersize=15, label="Index 0")

        # 설정
        plt.gca().invert_xaxis() # CARLA 좌표계에 맞춰 X축 반전
        plt.title(f"Spawn Points in {self.map.name} (Check the red numbers!)")
        plt.xlabel("X [m]")
        plt.ylabel("Y [m]")
        plt.grid(True)
        plt.legend()
        plt.axis("equal")
        
        print("맵을 확인하고 원하는 번호를 선택하세요. 창을 닫으면 종료됩니다.")
        plt.show()

def main():
    rclpy.init()
    node = SpawnPointViewer()
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
