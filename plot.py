import pyvista as pv
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os
from pathlib import Path

# Configuration - for flat directory structure
base_dir = Path.cwd()  # All files in the same directory
mesh_dirs = ['']       # Empty string since mesh is in root
x_positions_mm = [1, 50, 200, 650, 950]
x_positions_m = [x/1000 for x in x_positions_mm]

# Experimental parameters
U1 = 22.40  # m/s
deltaU = 19.14  # m/s
delta_omega = {1:5.236, 50:8.8583, 200:13.771, 650:35.894, 950:50.547}  # mm

def load_exp_data():
    exp_data = {}
    try:
        exp_data_path = base_dir / "exp_data.dat"
        with open(exp_data_path, 'r') as f:
            lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        current_x = None
        current_data = []
        
        for line in lines:
            if "ZONE T=" in line:
                if current_x is not None and current_data:
                    exp_data[current_x] = pd.DataFrame(current_data, 
                                                     columns=["Y_mm", "U_m_s", "U_norm"])
                try:
                    current_x = int(float(line.split('"')[-2].split('=')[-1].replace('mm','')))
                except:
                    continue
                current_data = []
            elif "VARIABLES" not in line:
                try:
                    parts = list(map(float, line.split()))
                    if len(parts) >= 5:
                        current_data.append([parts[1], parts[2], parts[4]])
                except ValueError:
                    continue
        
        if current_x is not None and current_data:
            exp_data[current_x] = pd.DataFrame(current_data, 
                                             columns=["Y_mm", "U_m_s", "U_norm"])
            
        print("Loaded experimental data for x-positions:", list(exp_data.keys()))
        return exp_data
        
    except Exception as e:
        raise ValueError(f"Error loading experimental data: {str(e)}")

def process_simulation_data():
    results = {}
    for mesh in mesh_dirs:
        # Look for solution file in the same directory
        path = base_dir / "vol_solution.vtu"
        print(f"\nProcessing: {path}")
        
        try:
            mesh_data = pv.read(str(path))
            velocity = mesh_data['Velocity']
            mesh_data['U'] = velocity[:, 0]
            mesh_data['U_norm'] = (mesh_data['U'] - U1)/deltaU
            
            results[mesh] = {}
            for x_m, x_mm in zip(x_positions_m, x_positions_mm):
                profile = mesh_data.sample_over_line(
                    pointa=(x_m, -0.05, 0),
                    pointb=(x_m, 0.05, 0),
                    resolution=300
                )
                y_vals = profile.points[:, 1] * 1000  # mm
                y_norm = y_vals / delta_omega[x_mm]
                u_norm = profile['U_norm']
                
                results[mesh][x_mm] = {
                    'y_norm': y_norm,
                    'u_norm': u_norm
                }
                
        except Exception as e:
            print(f"Error processing solution: {str(e)}")
            continue
    return results

def create_plots(exp_data, sim_results):
    output_dir = base_dir / "plots"
    os.makedirs(output_dir, exist_ok=True)
    
    mesh_colors = ['#1f77b4']
    exp_style = {'marker':'x', 'color':'k', 's':80, 'linewidths':1.5, 'zorder':10}
    
    for x_mm in x_positions_mm:
        plt.figure(figsize=(10, 6))
        
        # Plot simulation results
        for mesh, color in zip(mesh_dirs, mesh_colors):
            if mesh in sim_results and x_mm in sim_results[mesh]:
                data = sim_results[mesh][x_mm]
                plt.plot(data['u_norm'], data['y_norm'],
                        label="Simulation",
                        color=color,
                        linewidth=2,
                        alpha=0.8)
        
        # Plot experimental data
        if x_mm in exp_data:
            exp_df = exp_data[x_mm]
            plt.scatter(exp_df['U_norm'], 
                       exp_df['Y_mm']/delta_omega[x_mm],
                       label='Experimental',
                       **exp_style)
            print(f"Plotting {len(exp_df)} experimental points for x={x_mm}mm")
        else:
            print(f"Warning: No experimental data found for x={x_mm}mm")
        
        plt.xlabel(r"$(U-U_1)/\Delta U$", fontsize=12)
        plt.ylabel(r"$y/\delta_\omega$", fontsize=12)
        plt.title(f"Mixing Layer Profile at x = {x_mm} mm", fontsize=14)
        plt.grid(True, linestyle=':', alpha=0.5)
        plt.legend(fontsize=10, framealpha=1)
        
        output_path = output_dir / f"profile_x{x_mm}mm.png"
        plt.savefig(str(output_path), dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Saved: {output_path}")

if __name__ == "__main__":
    print("Starting post-processing...")
    try:
        exp_data = load_exp_data()
        sim_results = process_simulation_data()
        create_plots(exp_data, sim_results)
        print("\nPost-processing completed successfully!")
    except Exception as e:
        print(f"\nError during post-processing: {e}")
        exit(1)