import math
from typing import List, Tuple, Optional
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def visualize_board(queens: List[int], title: Optional[str]=None, show_conflicts: bool=True, figsize: Tuple[int, int]=(6, 6), ax: Optional[plt.Axes]=None) -> plt.Figure:
    n = len(queens)
    created_ax = False
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize, dpi=120)
        created_ax = True
    else:
        fig = ax.figure
    col_light = '#EEEED2'
    col_dark = '#769656'
    col_conflict_tile = '#F5B7B1'
    col_conflict_line = '#E74C3C'
    conflicts: List[Tuple[Tuple[int, int], Tuple[int, int]]] = []
    conflicted_cells = set()
    if show_conflicts:
        for c1 in range(n):
            r1 = queens[c1]
            if r1 == -1:
                continue
            for c2 in range(c1 + 1, n):
                r2 = queens[c2]
                if r2 == -1:
                    continue
                if r1 == r2 or abs(r1 - r2) == abs(c1 - c2):
                    conflicts.append(((r1, c1), (r2, c2)))
                    conflicted_cells.add((r1, c1))
                    conflicted_cells.add((r2, c2))
    for r in range(n):
        for c in range(n):
            if (r, c) in conflicted_cells:
                tile_color = col_conflict_tile
            else:
                tile_color = col_light if (r + c) % 2 == 0 else col_dark
            rect = patches.Rectangle((c, n - 1 - r), 1, 1, linewidth=0.5, edgecolor='#333333', facecolor=tile_color)
            ax.add_patch(rect)
    if show_conflicts and conflicts:
        for (r1, c1), (r2, c2) in conflicts:
            x1, y1 = (c1 + 0.5, n - 1 - r1 + 0.5)
            x2, y2 = (c2 + 0.5, n - 1 - r2 + 0.5)
            ax.plot([x1, x2], [y1, y2], color=col_conflict_line, linestyle='--', linewidth=2.5, alpha=0.85, zorder=3)
            ax.plot([x1, x2], [y1, y2], color='white', linestyle='-', linewidth=1.0, alpha=0.6, zorder=4)
    for c in range(n):
        r = queens[c]
        if r != -1:
            q_color = '#C0392B' if (r, c) in conflicted_cells else '#F39C12'
            ax.text(c + 0.52, n - 1 - r + 0.48, 'Q', fontsize=240 // n, ha='center', va='center', color='#1E272C', alpha=0.45, zorder=5)
            ax.text(c + 0.5, n - 1 - r + 0.5, 'Q', fontsize=240 // n, fontfamily='DejaVu Sans', ha='center', va='center', color=q_color, zorder=6)
    ax.set_xlim(0, n)
    ax.set_ylim(0, n)
    ax.set_aspect('equal')
    col_labels = [chr(ord('A') + i) if n <= 26 else str(i) for i in range(n)]
    row_labels = [str(n - i) for i in range(n)]
    ax.set_xticks([i + 0.5 for i in range(n)])
    ax.set_xticklabels(col_labels, fontsize=max(7, 11 - n // 4), fontweight='bold')
    ax.set_yticks([i + 0.5 for i in range(n)])
    ax.set_yticklabels(reversed(row_labels), fontsize=max(7, 11 - n // 4), fontweight='bold')
    if title is None:
        conflict_msg = f'{len(conflicts)} Conflicts' if conflicts else 'Valid (0 Conflicts) [OK]'
        title = f'N-Queens Board (N = {n}) -- {conflict_msg}'
    ax.set_title(title, fontsize=12, fontweight='bold', pad=10)
    plt.tight_layout()
    return fig

def plot_solution_gallery(solutions: List[List[int]], n: int, max_solutions: int=8, cols: int=4) -> plt.Figure:
    num_to_show = min(len(solutions), max_solutions)
    if num_to_show == 0:
        fig, ax = plt.subplots(figsize=(4, 4))
        ax.text(0.5, 0.5, 'No Solution Found', ha='center', va='center')
        return fig
    rows = math.ceil(num_to_show / cols)
    fig, axes = plt.subplots(rows, cols, figsize=(3.2 * cols, 3.2 * rows), dpi=110)
    if rows == 1 and cols == 1:
        axes = [axes]
    elif rows == 1 or cols == 1:
        axes = list(axes)
    else:
        axes = [ax for row in axes for ax in row]
    for idx in range(len(axes)):
        if idx < num_to_show:
            sol = solutions[idx]
            visualize_board(sol, title=f'Solution #{idx + 1}', show_conflicts=False, ax=axes[idx])
        else:
            axes[idx].axis('off')
    fig.suptitle(f'N-Queens Gallery: {num_to_show}/{len(solutions)} Configurations (N = {n})', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    return fig
