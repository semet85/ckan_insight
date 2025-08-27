# -*- coding: utf-8 -*-
import ckan.plugins.toolkit as toolkit

def _ctx():
    return {"ignore_auth": True}

def ckanet_insight_list(limit=8, order="count_desc", q=""):
    """
    Kembalikan daftar insight groups (name, title, image_url, description, package_count).
    Params:
      - limit: int
      - order: 'count_desc' | 'count_asc' | 'name_asc' | 'name_desc'
      - q: filter teks (judul/desc/name)
    """
    groups = toolkit.get_action("group_list")(_ctx(), {"all_fields": True})
    insight = [g for g in groups if (g.get("name") or "").startswith("insight-")]

    rows = []
    q_l = (q or "").strip().lower()
    for g in insight:
        g_full = toolkit.get_action("group_show")(
            _ctx(), {"id": g["name"], "include_datasets": True}
        )
        row = {
            "name": g_full["name"],
            "title": g_full.get("title") or g_full["name"],
            "description": g_full.get("description") or "",
            "image_url": g_full.get("image_display_url") or g_full.get("image_url") or "",
            "package_count": len(g_full.get("packages") or []),
        }
        if q_l:
            text = (row["title"] + " " + row["description"] + " " + row["name"]).lower()
            if q_l not in text:
                continue
        rows.append(row)

    if order == "name_desc":
        rows.sort(key=lambda x: x["title"].lower(), reverse=True)
    elif order == "count_asc":
        rows.sort(key=lambda x: (x["package_count"], x["title"].lower()))
    elif order == "count_desc":
        rows.sort(key=lambda x: (-x["package_count"], x["title"].lower()))
    else:  # 'name_asc' atau default
        rows.sort(key=lambda x: x["title"].lower())

    return rows[: int(limit) if limit else 8]

def ckanet_count_groups_startswith(prefix="desa", limit=5000):
    """
    Hitung jumlah Group yang TITLE atau NAME diawali 'prefix' (case-insensitive).
    """
    kw = (prefix or "").strip().lower()
    if not kw:
        return 0

    groups = toolkit.get_action("group_list")(
        _ctx(), {"all_fields": True, "limit": int(limit)}
    )

    cnt = 0
    for g in groups:
        title = (g.get("title") or "").strip().lower()
        name  = (g.get("name")  or "").strip().lower()
        if title.startswith(kw) or name.startswith(kw):
            cnt += 1
    return cnt

def _ctx():
    return {"ignore_auth": True}

def ckanet_org_counts(prefix="desa", limit=5000):
    """
    Hitung organisasi:
      - total: semua organisasi
      - desa: title/name diawali 'prefix' (case-insensitive)
      - non_desa: total - desa (min 0)

    Return: dict {total, desa, non_desa}
    """
    pref = (prefix or "").strip().lower()
    orgs = toolkit.get_action("organization_list")(
        _ctx(), {"all_fields": True, "limit": int(limit)}
    )
    total = len(orgs)

    desa = 0
    for o in orgs:
        t = (o.get("title") or o.get("name") or "").strip().lower()
        if t.startswith(pref):
            desa += 1

    non_desa = total - desa
    if non_desa < 0:
        non_desa = 0

    return {"total": total, "desa": desa, "non_desa": non_desa}