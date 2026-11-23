"""
Elective planner for R23 (cs) DSC threads.

Models the data as a bipartite graph:
    Thread nodes  ---(edge labelled with slot DSC-E1..E5)---  Course nodes
A course node connected to 2+ threads is an OVERLAPPING course.

Run:  python elective_graph.py
Out:  elective_graph.png  (graph)  +  console report (overlaps, switching cost)
"""
from itertools import combinations
import networkx as nx
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ----------------------------------------------------------------------------
# 1. DATA  (thread -> ordered list of (slot, course_code, title))
# ----------------------------------------------------------------------------
THREADS = {
    "AI & ML": [
        ("E1", "R23MSCST019", "Data Warehousing and Data Mining"),
        ("E2", "R23MSCST020", "Statistical and Predictive Analytics"),
        ("E3", "R23MSCST021", "Machine Learning"),
        ("E4", "R23MSCST022", "Deep Learning"),
        ("E5", "R23MSCST023", "Natural Language Processing"),
    ],
    "Business Intelligence": [
        ("E1", "R23MSCST019", "Data Warehousing and Data Mining"),
        ("E2", "R23MSCST024", "Data Analytics and Tools"),
        ("E3", "R23MSCST021", "Machine Learning"),
        ("E4", "R23MSCST022", "Deep Learning"),
        ("E5", "R23MSCST025", "Mean Stack Web Development"),
    ],
    "Data Science": [
        ("E1", "R23MSCST026", "Statistical and Mathematical Foundations of Data Analytics"),
        ("E2", "R23MSCST019", "Data Warehousing and Data Mining"),
        ("E3", "R23MSCST020", "Statistical and Predictive Analytics"),
        ("E4", "R23MSCST024", "Data Analytics and Tools"),
        ("E5", "R23MSCST027", "Time Series Analysis in Data Science"),
    ],
    "Enterprise Systems": [
        ("E1", "R23MSCST028", "Middleware Technologies"),
        ("E2", "R23MSCST029", "Service Oriented Architecture"),
        ("E3", "R23MSCST030", "Software Configuration Management"),
        ("E4", "R23MSCST031", "Usability Engineering"),
        ("E5", "R23MSCST025", "Mean Stack Web Development"),
    ],
    "IoT & Cyber Security": [
        ("E1", "R23MSCST032", "Cryptography and Information Security"),
        ("E2", "R23MSCST033", "Block Chain Essentials"),
        ("E3", "R23MSCST034", "Principles of IoT"),
        ("E4", "R23MSCST035", "IoT Development Boards and its Interfacing"),
        ("E5", "R23MSCST036", "Ad Hoc Networks"),
    ],
    "Computer Networks": [
        ("E1", "R23MSCST037", "Information Security Management Standards"),
        ("E2", "R23MSCST036", "Ad Hoc Networks"),
        ("E3", "R23MSCST038", "Routing and Switching Concepts"),
        ("E4", "R23MSCST039", "Enterprise Networking, Security and Automation"),
        ("E5", "R23MSCST040", "Firewalls and VPN"),
    ],
}

# ----------------------------------------------------------------------------
# 2. BUILD GRAPH
# ----------------------------------------------------------------------------
G = nx.Graph()
TITLE = {}
for thread, courses in THREADS.items():
    G.add_node(thread, kind="thread")
    for slot, code, title in courses:
        TITLE[code] = title
        G.add_node(code, kind="course", title=title)
        G.add_edge(thread, code, slot=slot)

courses_of = {t: {c for _, c, _ in cs} for t, cs in THREADS.items()}
threads_of = {c: sorted(G.neighbors(c)) for c in TITLE}
shared = {c: ts for c, ts in threads_of.items() if len(ts) > 1}


def slot_of(thread, code):
    return G.edges[thread, code]["slot"]


# ----------------------------------------------------------------------------
# 3. PLANNING HELPERS
# ----------------------------------------------------------------------------
def overlap(a, b):
    """Courses common to threads a and b, with the slot each thread uses."""
    return [(c, TITLE[c], slot_of(a, c), slot_of(b, c))
            for c in sorted(courses_of[a] & courses_of[b])]


def switching_cost(from_thread, to_thread):
    """If you've done `from_thread` electives, how many NEW courses does
    `to_thread` still need?  (5 minus the courses you already hold.)"""
    return len(courses_of[to_thread] - courses_of[from_thread])


def combined_workload(chosen):
    """Unique courses needed to complete several threads together."""
    union = set().union(*(courses_of[t] for t in chosen))
    return len(union), sorted(union)


def best_pair():
    """Pair of threads that reuses the most courses (smallest combined load)."""
    return min(combinations(THREADS, 2),
               key=lambda p: combined_workload(p)[0])


# ----------------------------------------------------------------------------
# 4. REPORT
# ----------------------------------------------------------------------------
def report():
    print("=== OVERLAPPING COURSES ===")
    for c, ts in sorted(shared.items()):
        slots = ", ".join(f"{t} ({slot_of(t, c)})" for t in ts)
        print(f"{c}  {TITLE[c]}\n      -> {slots}")

    print("\n=== OVERLAP MATRIX (shared course count) ===")
    names = list(THREADS)
    short = {t: "".join(w[0] for w in t.replace("&", "").split()) for t in names}
    print(" " * 6 + "  ".join(f"{short[t]:>4}" for t in names))
    for a in names:
        row = [len(courses_of[a] & courses_of[b]) if a != b else "-" for b in names]
        print(f"{short[a]:>5} " + "  ".join(f"{str(x):>4}" for x in row))
    print("   key:", ", ".join(f"{short[t]}={t}" for t in names))

    print("\n=== PAIRS SORTED BY COMBINED WORKLOAD (fewer = more reuse) ===")
    pairs = sorted(combinations(names, 2), key=lambda p: combined_workload(p)[0])
    for p in pairs:
        n, _ = combined_workload(p)
        print(f"{n:>2} courses  {p[0]} + {p[1]}  "
              f"(shared: {10 - n})")

    print("\n=== SWITCHING COST (new courses needed when moving A -> B) ===")
    for a, b in combinations(names, 2):
        if courses_of[a] & courses_of[b]:
            print(f"{a} <-> {b}: {switching_cost(a, b)} new courses")


# ----------------------------------------------------------------------------
# 5. DRAW
# ----------------------------------------------------------------------------
THREAD_COLORS = {
    "AI & ML": "#4C78A8",
    "Business Intelligence": "#F58518",
    "Data Science": "#54A24B",
    "Enterprise Systems": "#B279A2",
    "IoT & Cyber Security": "#E45756",
    "Computer Networks": "#72B7B2",
}


def draw(path="elective_graph.png"):
    # order courses so each thread's courses sit together, shared ones in between
    order, seen = [], set()
    for t in THREADS:
        for _, c, _ in THREADS[t]:
            if c not in seen:
                seen.add(c)
                order.append(c)

    pos = {}
    n_t, n_c = len(THREADS), len(order)
    for i, t in enumerate(THREADS):
        pos[t] = (0, -(i + 0.5) * n_c / n_t)
    for j, c in enumerate(order):
        pos[c] = (1, -(j + 0.5))

    fig, ax = plt.subplots(figsize=(15, 13))
    # edges coloured by thread
    for t, c in G.edges():
        t, c = (t, c) if G.nodes[t]["kind"] == "thread" else (c, t)
        ax.annotate("", xy=pos[c], xytext=pos[t],
                    arrowprops=dict(arrowstyle="-", color=THREAD_COLORS[t],
                                    lw=1.8, alpha=0.75,
                                    connectionstyle="arc3,rad=0"))
        # slot label near the course end
        x = pos[t][0] * 0.22 + pos[c][0] * 0.78
        y = pos[t][1] * 0.22 + pos[c][1] * 0.78
        ax.text(x, y, G.edges[t, c]["slot"], fontsize=7,
                color=THREAD_COLORS[t], ha="center", va="center",
                bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.85))

    # thread nodes
    for t in THREADS:
        ax.text(*pos[t], t, ha="center", va="center", fontsize=11,
                fontweight="bold", color="white",
                bbox=dict(boxstyle="round,pad=0.5", fc=THREAD_COLORS[t], ec="none"))

    # course nodes (shared = bold outline + star)
    for c in order:
        is_shared = c in shared
        label = f"{c}\n{TITLE[c]}"
        if len(TITLE[c]) > 34:
            words, line, lines = TITLE[c].split(), "", []
            for w in words:
                if len(line) + len(w) > 34:
                    lines.append(line.strip()); line = ""
                line += w + " "
            lines.append(line.strip())
            label = c + "\n" + "\n".join(lines)
        ax.text(pos[c][0] + 0.03, pos[c][1], ("★ " if is_shared else "") + label,
                ha="left", va="center", fontsize=8.5,
                fontweight="bold" if is_shared else "normal",
                bbox=dict(boxstyle="round,pad=0.35",
                          fc="#FFF4CC" if is_shared else "#F4F4F4",
                          ec="#C99700" if is_shared else "#BBBBBB",
                          lw=2 if is_shared else 1))

    ax.set_xlim(-0.2, 1.65)
    ax.set_ylim(-n_c - 0.2, 0.2)
    ax.axis("off")
    ax.set_title("R23 DSC Elective Threads → Courses\n"
                 "★ = course shared by 2+ threads   |   E1–E5 = semester slot in that thread",
                 fontsize=13, pad=14)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    print(f"saved {path}")


if __name__ == "__main__":
    report()

    draw()
