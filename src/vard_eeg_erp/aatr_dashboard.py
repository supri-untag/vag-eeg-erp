"""Render the supplied AATR MATLAB figure as data, without executing MATLAB code."""

import numpy as np
from matplotlib.figure import Figure
from matplotlib.patches import Polygon, Rectangle
from scipy.io import loadmat


def children(node):
    value = node.get('children', [])
    return [value] if isinstance(value, dict) else list(value)


def text(value):
    return str(value).replace(r'\mu', 'µ').replace(r'\pm', '±')


def read_figure(path):
    root = loadmat(path, simplify_cells=True).get('hgS_070000')
    if not isinstance(root, dict):
        raise ValueError('File bukan FIG MATLAB AATR yang didukung.')
    axes = [n for n in children(root) if n.get('type') == 'axes']
    if len(axes) != 12:
        raise ValueError('Dashboard AATR memerlukan 6 panel ERP dan 6 panel temporal.')
    return root


def render_figure(root):
    figure = Figure(figsize=(16, 9.5), dpi=100, facecolor='white')
    for node in children(root):
        p = node.get('properties', {})
        if node.get('type') == 'axes':
            ax = figure.add_axes(p['Position'])
            for child in children(node):
                q = child.get('properties', {})
                kind = child.get('type')
                if kind == 'patch':
                    vertices = np.asarray(q['Vertices'])
                    ax.add_patch(Polygon(vertices[:, :2], facecolor=q.get('FaceColor', '.8'),
                                         edgecolor='none', alpha=q.get('FaceAlpha', 1)))
                elif kind == 'graph2d.lineseries':
                    ax.plot(np.atleast_1d(q['XData']), np.atleast_1d(q['YData']),
                            color=q.get('Color', 'black'), linewidth=q.get('LineWidth', 1),
                            linestyle=q.get('LineStyle', '-'), marker=q.get('Marker', 'None'),
                            markersize=q.get('MarkerSize', 4),
                            markeredgecolor=q.get('MarkerEdgeColor', 'auto'),
                            markerfacecolor=q.get('MarkerFaceColor', 'none'))
                elif kind == 'constantline':
                    func = ax.axvline if q.get('InterceptAxis') == 'x' else ax.axhline
                    func(q.get('Value', 0), color=q.get('Color', '.7'),
                         linestyle=q.get('LineStyle', '--'), linewidth=.6)
                elif kind == 'text' and str(q.get('String', '')):
                    string = text(q['String'])
                    if string == 'µV':
                        ax.set_ylabel(string, fontsize=9)
                    elif string == 'Time (ms)':
                        ax.set_xlabel(string, fontsize=9)
                    else:
                        ax.text(*q['Position'][:2], string, color=q.get('Color', 'black'),
                                fontsize=10, fontweight=q.get('FontWeight', 'normal'))
            ax.set_xlim(p['XLim'])
            ax.set_ylim(p['YLim'])
            for dimension in ['X', 'Y']:
                ticks = p.get(dimension + 'Tick')
                labels = p.get(dimension + 'TickLabel')
                if ticks is not None:
                    getattr(ax, 'set_' + dimension.lower() + 'ticks')(np.atleast_1d(ticks))
                if labels is not None:
                    labels = np.atleast_1d(labels).tolist()
                    if len(labels) == 0:
                        getattr(ax, 'tick_params')(axis=dimension.lower(), labelbottom=False,
                                                 labelleft=False)
                    elif ticks is not None and len(labels) == len(np.atleast_1d(ticks)):
                        getattr(ax, 'set_' + dimension.lower() + 'ticklabels')(labels)
            ax.tick_params(labelsize=8, width=.4, length=2)
            ax.grid(alpha=.1, linewidth=.5)
            for side in ['top', 'right']:
                ax.spines[side].set_visible(False)
            for side in ['bottom', 'left']:
                ax.spines[side].set_color('.6')
                ax.spines[side].set_linewidth(.5)
        elif node.get('type') == 'scribe.scribeaxes':
            for child in children(node):
                q = child.get('properties', {})
                position = q.get('Position')
                if position is None:
                    continue
                x, y, w, h = position
                if child.get('type') == 'scribe.scriberect':
                    figure.add_artist(Rectangle((x, y), w, h, transform=figure.transFigure,
                                      facecolor=q.get('FaceColor', 'none'),
                                      edgecolor=q.get('Color', 'none'), linewidth=.5, zorder=0))
                elif child.get('type') == 'scribe.textbox':
                    align = q.get('HorizontalAlignment', 'left')
                    offset = w / 2 if align == 'center' else w if align == 'right' else 0
                    figure.text(x + offset, y + h / 2, text(q.get('String', '')),
                                ha=align, va='center', color=q.get('Color', 'black'),
                                fontsize=q.get('FontSize', 10) * .8,
                                fontweight=q.get('FontWeight', 'normal'))
    return figure
