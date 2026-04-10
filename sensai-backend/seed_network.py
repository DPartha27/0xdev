"""
Seed script: Inserts 10 users, an org, and populates the network hub with dummy data.
Run from sensai-backend/: .venv/bin/python seed_network.py
"""

import asyncio
import sys
import os
import json
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from api.config import (
    sqlite_db_path,
    users_table_name,
    organizations_table_name,
    user_organizations_table_name,
    network_posts_table_name,
    network_tags_table_name,
    network_post_tags_table_name,
    network_comments_table_name,
    network_votes_table_name,
    network_poll_options_table_name,
    network_poll_votes_table_name,
    user_network_profiles_table_name,
)
from api.utils.db import get_new_db_connection
from api.db import init_db
from api.reputation import recompute_user_badge


USERS = [
    {"email": "priya.sharma@example.com", "first_name": "Priya", "last_name": "Sharma"},
    {"email": "arjun.patel@example.com", "first_name": "Arjun", "last_name": "Patel"},
    {"email": "meera.krishnan@example.com", "first_name": "Meera", "last_name": "Krishnan"},
    {"email": "rahul.verma@example.com", "first_name": "Rahul", "last_name": "Verma"},
    {"email": "ananya.gupta@example.com", "first_name": "Ananya", "last_name": "Gupta"},
    {"email": "vikram.singh@example.com", "first_name": "Vikram", "last_name": "Singh"},
    {"email": "deepa.nair@example.com", "first_name": "Deepa", "last_name": "Nair"},
    {"email": "karthik.rajan@example.com", "first_name": "Karthik", "last_name": "Rajan"},
    {"email": "sneha.iyer@example.com", "first_name": "Sneha", "last_name": "Iyer"},
    {"email": "amit.joshi@example.com", "first_name": "Amit", "last_name": "Joshi"},
]

TAGS = [
    "Dynamic Programming", "Recursion", "System Design", "React Hooks",
    "Python Basics", "SQL Queries", "Data Structures", "Algorithms",
    "CSS Flexbox", "JavaScript", "Binary Trees", "Graph Theory",
    "REST APIs", "Git Workflow", "Machine Learning",
]

POSTS = [
    {
        "post_type": "explanation",
        "title": "Why greedy fails for the coin change problem",
        "content_text": "Many students try the greedy approach for coin change — always picking the largest coin first. This works for standard US coins (25, 10, 5, 1) but fails for arbitrary denominations.\n\nExample: coins = [1, 3, 4], amount = 6\n- Greedy: 4 + 1 + 1 = 3 coins\n- Optimal: 3 + 3 = 2 coins\n\nThe greedy approach doesn't consider future consequences. Dynamic programming solves this by building up from smaller subproblems, ensuring we find the globally optimal solution.\n\nKey insight: DP works here because the problem has overlapping subproblems and optimal substructure.",
        "tags": ["Dynamic Programming", "Algorithms"],
    },
    {
        "post_type": "question",
        "title": "How do I decide between BFS and DFS for graph problems?",
        "content_text": "I keep getting confused about when to use BFS vs DFS. I know BFS uses a queue and DFS uses a stack/recursion, but I can't figure out which one to pick for a given problem. Can someone explain with examples?",
        "tags": ["Graph Theory", "Algorithms", "Data Structures"],
    },
    {
        "post_type": "code_snippet",
        "title": "Clean implementation of binary search in Python",
        "content_text": "Here's a clean, bug-free binary search that handles all edge cases. The key is using lo <= hi (not lo < hi) and mid = lo + (hi - lo) // 2 to avoid overflow.",
        "code_content": "def binary_search(arr, target):\n    lo, hi = 0, len(arr) - 1\n    \n    while lo <= hi:\n        mid = lo + (hi - lo) // 2\n        \n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            lo = mid + 1\n        else:\n            hi = mid - 1\n    \n    return -1  # not found\n\n\n# Example usage\nnums = [1, 3, 5, 7, 9, 11, 13]\nprint(binary_search(nums, 7))   # Output: 3\nprint(binary_search(nums, 4))   # Output: -1",
        "coding_language": "python",
        "tags": ["Algorithms", "Python Basics"],
    },
    {
        "post_type": "tip",
        "title": "Use console.table() instead of console.log() for arrays",
        "content_text": "When debugging arrays of objects in JavaScript, console.table() formats them as a neat table in the browser console. Way easier to read than a collapsed object tree.\n\nAlso try console.group() and console.groupEnd() for organizing related logs.",
        "tags": ["JavaScript"],
    },
    {
        "post_type": "thread",
        "title": "What's everyone's approach to learning system design?",
        "content_text": "I'm trying to build a solid understanding of system design but there's so much to cover — load balancers, caching, databases, message queues, etc. How did you approach learning this? Did you follow a specific roadmap or just dive into specific systems?\n\nSharing my current approach: I'm reading 'Designing Data-Intensive Applications' and trying to design one system per week on paper.",
        "tags": ["System Design"],
    },
    {
        "post_type": "explanation",
        "title": "Understanding React useEffect cleanup functions",
        "content_text": "The cleanup function in useEffect runs BEFORE the next effect execution and when the component unmounts. This is crucial for preventing memory leaks.\n\nCommon use cases:\n1. Clearing intervals/timeouts\n2. Unsubscribing from event listeners\n3. Cancelling API requests\n4. Closing WebSocket connections\n\nThe cleanup runs with the OLD values from the previous render, not the current ones. This is by design — it cleans up the previous effect before setting up the new one.",
        "tags": ["React Hooks", "JavaScript"],
    },
    {
        "post_type": "poll",
        "title": "Which programming language should beginners start with in 2026?",
        "content_text": "There's always a debate about the best first language. Curious what this community thinks — considering job market, learning curve, and versatility.",
        "tags": ["Python Basics", "JavaScript"],
        "poll_options": ["Python", "JavaScript", "Java", "Go", "Rust"],
    },
    {
        "post_type": "code_snippet",
        "title": "SQL query to find the second highest salary",
        "content_text": "A classic interview question. Here are two approaches — one using subquery and one using DENSE_RANK(). The window function approach is more flexible for finding Nth highest.",
        "code_content": "-- Approach 1: Subquery\nSELECT MAX(salary) AS second_highest\nFROM employees\nWHERE salary < (SELECT MAX(salary) FROM employees);\n\n-- Approach 2: Window Function (more flexible)\nWITH ranked AS (\n    SELECT salary,\n           DENSE_RANK() OVER (ORDER BY salary DESC) AS rank\n    FROM employees\n)\nSELECT salary AS second_highest\nFROM ranked\nWHERE rank = 2;",
        "coding_language": "sql",
        "tags": ["SQL Queries"],
    },
    {
        "post_type": "question",
        "title": "Why is my CSS flexbox not centering vertically?",
        "content_text": "I have a container with display: flex, justify-content: center, and align-items: center, but the child element isn't vertically centered. The container has no explicit height. What am I missing?",
        "tags": ["CSS Flexbox"],
    },
    {
        "post_type": "explanation",
        "title": "Git rebase vs merge — when to use which",
        "content_text": "Merge creates a merge commit that preserves the full branch history. Rebase rewrites history to create a linear sequence.\n\nUse MERGE when:\n- Working on shared/public branches\n- You want to preserve the context of when branches diverged\n- You're merging a feature branch into main\n\nUse REBASE when:\n- Cleaning up local commits before pushing\n- Keeping feature branch up to date with main\n- You want a clean, linear history\n\nGolden rule: NEVER rebase commits that have been pushed to a shared repository. It rewrites history that others may have based their work on.",
        "tags": ["Git Workflow"],
    },
]

COMMENTS_DATA = [
    # (post_index, content, code_content, coding_language)
    (0, "This was the exact explanation I needed! The greedy approach kept tripping me up in competitions.", None, None),
    (0, "Great post. Another way to think about it: greedy makes locally optimal choices, DP makes globally optimal ones.", None, None),
    (0, "Here's the DP solution for reference:", "def coin_change(coins, amount):\n    dp = [float('inf')] * (amount + 1)\n    dp[0] = 0\n    for i in range(1, amount + 1):\n        for coin in coins:\n            if coin <= i:\n                dp[i] = min(dp[i], dp[i - coin] + 1)\n    return dp[amount] if dp[amount] != float('inf') else -1", "python"),
    (1, "Simple rule of thumb: BFS for shortest path in unweighted graphs, DFS for exploring all paths or detecting cycles.", None, None),
    (1, "BFS is also better when the solution is close to the root. DFS when it's deep in the tree.", None, None),
    (2, "Thanks for the overflow prevention tip with mid = lo + (hi - lo) // 2. I always used (lo + hi) // 2 which can overflow in other languages.", None, None),
    (3, "I also recommend console.dir() for viewing the full object hierarchy. Game changer for DOM elements.", None, None),
    (4, "I followed the System Design Primer on GitHub and it was incredibly helpful. Start with the fundamentals before jumping into specific systems.", None, None),
    (4, "The key is to practice designing systems out loud. Find a study buddy and do mock design sessions. That's how I improved the most.", None, None),
    (5, "The part about cleanup running with OLD values blew my mind. That explains so many bugs I've had with stale closures.", None, None),
    (5, "Here's a practical example:", "useEffect(() => {\n  const timer = setInterval(() => {\n    console.log('tick');\n  }, 1000);\n\n  // Cleanup: runs when component unmounts\n  // or before next effect execution\n  return () => clearInterval(timer);\n}, []);", "javascript"),
    (7, "The DENSE_RANK approach is definitely the way to go. You can easily modify it to find the 3rd, 4th, etc. highest.", None, None),
    (8, "Your container needs a defined height for vertical centering to work. Try adding height: 100vh or min-height: 100vh to the container.", None, None),
    (8, "Also check if the parent of your flex container has a height. Flexbox vertical centering requires the container to have more height than its content.", None, None),
    (9, "I tell my team: merge for integration, rebase for cleanup. Works well in practice.", None, None),
]


async def seed():
    print("Initializing database...")
    await init_db()

    async with get_new_db_connection() as conn:
        cursor = await conn.cursor()

        # --- Check for existing org or create one ---
        await cursor.execute(f"SELECT id FROM {organizations_table_name} WHERE slug = 'sensai-demo' AND deleted_at IS NULL")
        org_row = await cursor.fetchone()
        if org_row:
            org_id = org_row[0]
            print(f"Using existing org: {org_id}")
        else:
            await cursor.execute(
                f"INSERT INTO {organizations_table_name} (slug, name, default_logo_color) VALUES (?, ?, ?)",
                ("sensai-demo", "SensAI Demo School", "#6366f1"),
            )
            org_id = cursor.lastrowid
            print(f"Created org: {org_id}")

        # --- Insert users ---
        user_ids = []
        for u in USERS:
            await cursor.execute(f"SELECT id FROM {users_table_name} WHERE email = ?", (u["email"],))
            existing = await cursor.fetchone()
            if existing:
                user_ids.append(existing[0])
                print(f"  User exists: {u['first_name']} ({existing[0]})")
            else:
                await cursor.execute(
                    f"INSERT INTO {users_table_name} (email, first_name, last_name) VALUES (?, ?, ?)",
                    (u["email"], u["first_name"], u["last_name"]),
                )
                user_ids.append(cursor.lastrowid)
                print(f"  Created user: {u['first_name']} ({cursor.lastrowid})")

        # --- Link users to org ---
        for i, uid in enumerate(user_ids):
            role = "owner" if i == 0 else "admin" if i == 1 else "admin"
            await cursor.execute(
                f"INSERT OR IGNORE INTO {user_organizations_table_name} (user_id, org_id, role) VALUES (?, ?, ?)",
                (uid, org_id, role),
            )

        # --- Create network profiles ---
        roles = ["mentor", "mentor", "newbie", "newbie", "newbie", "newbie", "newbie", "newbie", "newbie", "newbie"]
        for i, uid in enumerate(user_ids):
            await cursor.execute(
                f"INSERT OR IGNORE INTO {user_network_profiles_table_name} (user_id, org_id, network_role, badge_tier, badge_score) VALUES (?, ?, ?, ?, ?)",
                (uid, org_id, roles[i], "Bronze 1", 0),
            )

        # --- Create tags ---
        tag_ids = {}
        for tag_name in TAGS:
            slug = tag_name.lower().replace(" ", "-")
            await cursor.execute(
                f"SELECT id FROM {network_tags_table_name} WHERE org_id = ? AND slug = ?",
                (org_id, slug),
            )
            existing = await cursor.fetchone()
            if existing:
                tag_ids[tag_name] = existing[0]
            else:
                await cursor.execute(
                    f"INSERT INTO {network_tags_table_name} (org_id, name, slug) VALUES (?, ?, ?)",
                    (org_id, tag_name, slug),
                )
                tag_ids[tag_name] = cursor.lastrowid
        print(f"  Created/found {len(tag_ids)} tags")

        # --- Create posts ---
        post_ids = []
        for i, post_data in enumerate(POSTS):
            author_id = user_ids[i % len(user_ids)]

            await cursor.execute(
                f"""INSERT INTO {network_posts_table_name}
                    (org_id, author_id, post_type, title, content_text, code_content, coding_language)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    org_id,
                    author_id,
                    post_data["post_type"],
                    post_data["title"],
                    post_data.get("content_text"),
                    post_data.get("code_content"),
                    post_data.get("coding_language"),
                ),
            )
            post_id = cursor.lastrowid
            post_ids.append(post_id)
            print(f"  Created post #{post_id}: {post_data['title'][:50]}...")

            # Link tags
            for tag_name in post_data.get("tags", []):
                tid = tag_ids.get(tag_name)
                if tid:
                    await cursor.execute(
                        f"INSERT OR IGNORE INTO {network_post_tags_table_name} (post_id, tag_id) VALUES (?, ?)",
                        (post_id, tid),
                    )
                    await cursor.execute(
                        f"UPDATE {network_tags_table_name} SET usage_count = usage_count + 1 WHERE id = ?",
                        (tid,),
                    )

            # Create poll options
            if post_data["post_type"] == "poll" and "poll_options" in post_data:
                for opt_text in post_data["poll_options"]:
                    await cursor.execute(
                        f"INSERT INTO {network_poll_options_table_name} (post_id, option_text) VALUES (?, ?)",
                        (post_id, opt_text),
                    )

            # Update author profile
            await cursor.execute(
                f"UPDATE {user_network_profiles_table_name} SET posts_count = posts_count + 1 WHERE user_id = ? AND org_id = ?",
                (author_id, org_id),
            )

        # --- Create comments ---
        for post_idx, content, code_content, coding_language in COMMENTS_DATA:
            post_id = post_ids[post_idx]
            commenter_id = random.choice(user_ids)

            await cursor.execute(
                f"""INSERT INTO {network_comments_table_name}
                    (post_id, author_id, content, code_content, coding_language)
                    VALUES (?, ?, ?, ?, ?)""",
                (post_id, commenter_id, content, code_content, coding_language),
            )

            # Update reply count
            await cursor.execute(
                f"UPDATE {network_posts_table_name} SET reply_count = reply_count + 1 WHERE id = ?",
                (post_id,),
            )

            # Update commenter profile
            await cursor.execute(
                f"UPDATE {user_network_profiles_table_name} SET comments_count = comments_count + 1 WHERE user_id = ? AND org_id = ?",
                (commenter_id, org_id),
            )

        print(f"  Created {len(COMMENTS_DATA)} comments")

        # --- Create votes (upvotes/downvotes on posts) ---
        vote_count = 0
        for post_id in post_ids:
            # 3-7 random voters per post
            num_voters = random.randint(3, 7)
            voters = random.sample(user_ids, min(num_voters, len(user_ids)))
            for voter_id in voters:
                vote_type = random.choices(["upvote", "downvote"], weights=[85, 15])[0]
                try:
                    await cursor.execute(
                        f"INSERT OR IGNORE INTO {network_votes_table_name} (user_id, target_type, target_id, vote_type) VALUES (?, ?, ?, ?)",
                        (voter_id, "post", post_id, vote_type),
                    )
                    if vote_type == "upvote":
                        await cursor.execute(f"UPDATE {network_posts_table_name} SET upvote_count = upvote_count + 1 WHERE id = ?", (post_id,))
                    else:
                        await cursor.execute(f"UPDATE {network_posts_table_name} SET downvote_count = downvote_count + 1 WHERE id = ?", (post_id,))

                    # Update author's profile
                    await cursor.execute(f"SELECT author_id FROM {network_posts_table_name} WHERE id = ?", (post_id,))
                    author_row = await cursor.fetchone()
                    if author_row:
                        col = "upvotes_received" if vote_type == "upvote" else "downvotes_received"
                        await cursor.execute(
                            f"UPDATE {user_network_profiles_table_name} SET {col} = {col} + 1 WHERE user_id = ? AND org_id = ?",
                            (author_row[0], org_id),
                        )
                    vote_count += 1
                except Exception:
                    pass  # ignore duplicate votes

        print(f"  Created ~{vote_count} post votes")

        # --- Vote on comments ---
        await cursor.execute(f"SELECT id FROM {network_comments_table_name} WHERE deleted_at IS NULL")
        comment_rows = await cursor.fetchall()
        comment_vote_count = 0
        for (comment_id,) in comment_rows:
            num_voters = random.randint(1, 4)
            voters = random.sample(user_ids, min(num_voters, len(user_ids)))
            for voter_id in voters:
                try:
                    await cursor.execute(
                        f"INSERT OR IGNORE INTO {network_votes_table_name} (user_id, target_type, target_id, vote_type) VALUES (?, ?, ?, ?)",
                        (voter_id, "comment", comment_id, "upvote"),
                    )
                    await cursor.execute(
                        f"UPDATE {network_comments_table_name} SET upvote_count = upvote_count + 1 WHERE id = ?",
                        (comment_id,),
                    )
                    comment_vote_count += 1
                except Exception:
                    pass
        print(f"  Created ~{comment_vote_count} comment votes")

        # --- Vote on poll ---
        await cursor.execute(f"SELECT id FROM {network_poll_options_table_name}")
        poll_option_rows = await cursor.fetchall()
        poll_vote_count = 0
        if poll_option_rows:
            option_ids = [r[0] for r in poll_option_rows]
            for voter_id in user_ids:
                chosen = random.choice(option_ids)
                try:
                    await cursor.execute(
                        f"INSERT OR IGNORE INTO {network_poll_votes_table_name} (user_id, option_id) VALUES (?, ?)",
                        (voter_id, chosen),
                    )
                    await cursor.execute(
                        f"UPDATE {network_poll_options_table_name} SET vote_count = vote_count + 1 WHERE id = ?",
                        (chosen,),
                    )
                    poll_vote_count += 1
                except Exception:
                    pass
        print(f"  Created {poll_vote_count} poll votes")

        await conn.commit()

    # --- Recompute badges for all users ---
    print("  Recomputing badges...")
    for uid in user_ids:
        await recompute_user_badge(uid, org_id)

    # Print final profile summary
    print("\n=== User Badge Summary ===")
    async with get_new_db_connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute(
            f"""SELECT u.first_name, u.last_name, np.badge_tier, np.badge_score, np.network_role,
                    np.posts_count, np.comments_count, np.upvotes_received, np.downvotes_received
                FROM {user_network_profiles_table_name} np
                JOIN {users_table_name} u ON np.user_id = u.id
                WHERE np.org_id = ?
                ORDER BY np.badge_score DESC""",
            (org_id,),
        )
        rows = await cursor.fetchall()
        print(f"{'Name':<20} {'Tier':<12} {'Score':<6} {'Role':<8} {'Posts':<6} {'Comments':<9} {'Up':<4} {'Down':<4}")
        print("-" * 75)
        for r in rows:
            name = f"{r[0]} {r[1]}"
            print(f"{name:<20} {r[2]:<12} {r[3]:<6} {r[4]:<8} {r[5]:<6} {r[6]:<9} {r[7]:<4} {r[8]:<4}")

    print("\nDone! Seeded 10 users, 10 posts, 15 comments, votes, and poll data.")
    print(f"Database: {sqlite_db_path}")


if __name__ == "__main__":
    asyncio.run(seed())
