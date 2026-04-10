"""
Massive seed: 1000 users, 1000+ posts across all types, 3000+ comments, 5000+ votes.
Timestamps spread across the last 90 days for realistic trending/recommendation.
Run from sensai-backend/: .venv/bin/python seed_massive.py
"""

import asyncio
import sys
import os
import random
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from api.config import (
    sqlite_db_path,
    users_table_name,
    organizations_table_name,
    user_organizations_table_name,
    cohorts_table_name,
    user_cohorts_table_name,
    courses_table_name,
    course_cohorts_table_name,
    tasks_table_name,
    course_tasks_table_name,
    milestones_table_name,
    course_milestones_table_name,
    task_completions_table_name,
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
from api.reputation import recompute_user_badge, recompute_post_quality_score

# ── helpers ──

FIRST_NAMES = [
    "Aarav", "Aditi", "Aisha", "Akash", "Amara", "Ananya", "Arjun", "Bhavya",
    "Chandra", "Daksh", "Deepa", "Dev", "Dhruv", "Divya", "Esha", "Farhan",
    "Gauri", "Harsh", "Isha", "Jai", "Kabir", "Kavya", "Kiran", "Kriti",
    "Lakshmi", "Manav", "Meera", "Mihir", "Nandini", "Naveen", "Neha", "Nikhil",
    "Ojas", "Pallavi", "Pranav", "Priya", "Rahul", "Riya", "Rohan", "Sakshi",
    "Samar", "Sanya", "Shreya", "Siddharth", "Sneha", "Tanya", "Varun", "Veda",
    "Vikram", "Yash", "Zara", "Aditya", "Anjali", "Arnav", "Avni", "Chirag",
    "Disha", "Gaurav", "Hemant", "Ishaan", "Jaya", "Kartik", "Lavanya", "Maya",
    "Nisha", "Om", "Pooja", "Raj", "Saanvi", "Tanvi", "Uday", "Vidya",
    "Akshay", "Bhumi", "Darsh", "Eva", "Fatima", "Girish", "Hema", "Imran",
    "Juhi", "Kunal", "Lata", "Mohit", "Neeta", "Omkar", "Pari", "Raghav",
    "Sagar", "Trisha", "Uma", "Vivek", "Wahid", "Yamini", "Zubin", "Aarushi",
    "Bhaskar", "Chetna", "Dinesh", "Ekta",
]

LAST_NAMES = [
    "Sharma", "Patel", "Krishnan", "Verma", "Gupta", "Singh", "Nair", "Rajan",
    "Iyer", "Joshi", "Chopra", "Desai", "Mehta", "Reddy", "Malhotra", "Kapoor",
    "Bhat", "Chauhan", "Dutta", "Ghosh", "Hegde", "Jain", "Khan", "Kulkarni",
    "Menon", "Pillai", "Rao", "Saxena", "Thakur", "Trivedi", "Agarwal", "Bose",
    "Das", "Goswami", "Iyengar", "Mishra", "Mukherjee", "Naidu", "Pandey",
    "Rajput", "Sinha", "Tiwari", "Upadhyay", "Varma", "Yadav", "Banerjee",
    "Choudhury", "Dixit", "Fernandez", "George",
]

TAGS = [
    "Dynamic Programming", "Recursion", "System Design", "React Hooks",
    "Python Basics", "SQL Queries", "Data Structures", "Algorithms",
    "CSS Flexbox", "JavaScript", "Binary Trees", "Graph Theory",
    "REST APIs", "Git Workflow", "Machine Learning", "TypeScript",
    "Docker", "Kubernetes", "AWS", "Database Design", "Testing",
    "CI/CD", "Security", "Performance", "Rust", "Go",
    "Node.js", "Django", "FastAPI", "Next.js",
]

# ── post templates per type ──

THREAD_TITLES = [
    "What side projects are you working on this week?",
    "How do you stay motivated while learning to code?",
    "Share your dev setup — what tools do you use daily?",
    "What's the hardest bug you've ever fixed?",
    "How did you land your first developer job?",
    "What's your unpopular tech opinion?",
    "Which YouTube channels do you recommend for learning?",
    "How do you manage burnout as a developer?",
    "What coding habits changed your productivity?",
    "Share your bookmarks — what sites do you visit daily?",
    "What's a technology that surprised you recently?",
    "How do you approach learning a new framework?",
    "What's your experience with pair programming?",
    "Remote vs office — what works better for you?",
    "What misconceptions did you have as a beginner?",
]

QUESTION_TITLES = [
    "How does garbage collection work in Python?",
    "What's the difference between == and === in JavaScript?",
    "When should I use a hashmap vs a sorted array?",
    "How do I handle authentication in a REST API?",
    "What's the best way to learn SQL joins?",
    "Why does my recursive function cause a stack overflow?",
    "How do microservices communicate with each other?",
    "What's the difference between TCP and UDP?",
    "How do I optimize a slow database query?",
    "When should I use GraphQL instead of REST?",
    "How does the event loop work in Node.js?",
    "What's the difference between a mutex and a semaphore?",
    "How do I implement rate limiting in my API?",
    "What's the CAP theorem and why does it matter?",
    "How do I set up CI/CD for a small project?",
]

EXPLANATION_TITLES = [
    "Understanding closures in JavaScript — a visual guide",
    "How B-trees power database indexes",
    "Why you should avoid premature optimization",
    "The difference between concurrency and parallelism",
    "How HTTPS actually works — step by step",
    "Understanding Big O notation with real examples",
    "How React reconciliation works under the hood",
    "Why immutability matters in functional programming",
    "How DNS resolution works when you type a URL",
    "Understanding the Python GIL and its implications",
    "How OAuth 2.0 works — simplified",
    "Understanding database normalization (1NF to 3NF)",
    "How WebSockets differ from HTTP polling",
    "Understanding the virtual DOM and why it's fast",
    "How consistent hashing works in distributed systems",
]

TIP_TITLES = [
    "Use 'git stash' to save work without committing",
    "VS Code shortcut: Ctrl+D to select next occurrence",
    "Use Python's enumerate() instead of manual counters",
    "Set up aliases in .bashrc to save time",
    "Use console.time() to measure JS performance",
    "Try 'git bisect' to find the commit that broke things",
    "Use CSS Grid for 2D layouts, Flexbox for 1D",
    "Always use parameterized queries to prevent SQL injection",
    "Use TypeScript's 'satisfies' for type-safe object literals",
    "Add 'defer' to script tags for faster page loads",
    "Use Python f-strings instead of .format() or %",
    "Set up pre-commit hooks to catch issues early",
    "Use Docker Compose for local multi-service development",
    "Use structured logging in production — not print()",
    "Use .env files for secrets, never hardcode them",
]

CODE_TITLES = [
    "Merge sort implementation in Python",
    "Custom React hook for debouncing input",
    "SQL window functions cheat sheet",
    "Implementing a LRU cache from scratch",
    "Python decorator for timing functions",
    "JavaScript Promise.all with error handling",
    "Trie implementation for autocomplete",
    "Bash script for automated backups",
    "Go goroutines — producer/consumer pattern",
    "Rust ownership explained with code",
    "TypeScript generic utility types",
    "Docker multi-stage build for Node.js",
    "Python context manager for database connections",
    "React useReducer for complex state",
    "Implementing binary search in 5 languages",
]

POLL_TITLES = [
    "Best programming language for beginners in 2026?",
    "Tabs or spaces?",
    "Which cloud provider do you prefer?",
    "Favorite code editor?",
    "Best way to learn data structures?",
    "Morning coder or night owl?",
    "Which frontend framework do you use?",
    "Do you write tests first (TDD)?",
    "Monorepo or polyrepo?",
    "SQL or NoSQL for your next project?",
]

POLL_OPTIONS_MAP = {
    0: ["Python", "JavaScript", "Go", "Rust", "Java"],
    1: ["Tabs", "Spaces", "Whatever the project uses"],
    2: ["AWS", "GCP", "Azure", "Self-hosted"],
    3: ["VS Code", "Neovim", "JetBrains", "Zed", "Cursor"],
    4: ["LeetCode", "Books", "Courses", "Build projects"],
    5: ["Morning", "Night", "Whenever I can"],
    6: ["React", "Vue", "Svelte", "Angular", "HTMX"],
    7: ["Always", "Sometimes", "Rarely", "Never"],
    8: ["Monorepo", "Polyrepo", "Depends on the project"],
    9: ["SQL", "NoSQL", "Both", "Depends on the use case"],
}

COMMENT_TEMPLATES = [
    "Great explanation! This really helped me understand the concept.",
    "I had the exact same question. Thanks for asking this.",
    "One thing to add — you should also consider {topic} in this context.",
    "This is a solid approach. I've been doing something similar.",
    "Thanks for sharing! Bookmarking this for later.",
    "I disagree slightly — in my experience, {topic} works better here.",
    "Can you elaborate on the {topic} part? I'm a bit confused.",
    "This is exactly what I needed. Clear and concise.",
    "I've been struggling with this for days. Your explanation clicked.",
    "Nice tip! I'll start using this in my workflow.",
    "Learned something new today. Thanks for posting!",
    "This changed how I think about {topic}. Well written.",
    "For beginners: start with the basics before diving into this.",
    "Pro tip: combine this with {topic} for even better results.",
    "I tested this approach and it works perfectly. Confirmed.",
    "Interesting perspective. I hadn't thought about it this way.",
    "Would love to see a follow-up post on {topic}.",
    "This is underrated content. More people should see this.",
    "Saved me hours of debugging. Thank you!",
    "Quality post. The community needs more content like this.",
]

CONTENT_TEMPLATES = [
    "This is something I've been thinking about a lot lately. Let me share my thoughts and experiences on this topic. I believe understanding the fundamentals is key before moving on to advanced concepts.",
    "After working with this for several months, I wanted to share some insights. The biggest lesson I learned was to start simple and iterate.",
    "I see a lot of confusion around this topic, so here's my attempt at a clear explanation. Feel free to ask questions in the comments.",
    "Here's a pattern I've found really useful in production. It might seem complex at first, but once you understand the core idea, it becomes second nature.",
    "I recently learned this the hard way in a production incident. Sharing so others don't make the same mistake.",
]

CODE_SAMPLES = [
    ("python", "def solution(nums, target):\n    seen = {}\n    for i, num in enumerate(nums):\n        complement = target - num\n        if complement in seen:\n            return [seen[complement], i]\n        seen[num] = i\n    return []"),
    ("javascript", "const debounce = (fn, delay) => {\n  let timer;\n  return (...args) => {\n    clearTimeout(timer);\n    timer = setTimeout(() => fn(...args), delay);\n  };\n};"),
    ("python", "from functools import lru_cache\n\n@lru_cache(maxsize=None)\ndef fib(n):\n    if n < 2:\n        return n\n    return fib(n - 1) + fib(n - 2)"),
    ("sql", "SELECT department, employee_name, salary,\n       RANK() OVER (PARTITION BY department ORDER BY salary DESC) as rank\nFROM employees\nWHERE rank <= 3;"),
    ("typescript", "type DeepPartial<T> = {\n  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];\n};"),
    ("python", "class LRUCache:\n    def __init__(self, capacity):\n        self.cache = {}\n        self.capacity = capacity\n\n    def get(self, key):\n        if key not in self.cache:\n            return -1\n        self.cache[key] = self.cache.pop(key)\n        return self.cache[key]"),
    ("javascript", "async function fetchWithRetry(url, retries = 3) {\n  for (let i = 0; i < retries; i++) {\n    try {\n      return await fetch(url);\n    } catch (err) {\n      if (i === retries - 1) throw err;\n      await new Promise(r => setTimeout(r, 1000 * (i + 1)));\n    }\n  }\n}"),
    ("go", "func worker(jobs <-chan int, results chan<- int) {\n    for j := range jobs {\n        results <- j * 2\n    }\n}"),
]


def rand_ts(days_ago_max=90, days_ago_min=0):
    """Random timestamp between days_ago_min and days_ago_max days ago."""
    delta = timedelta(
        days=random.randint(days_ago_min, days_ago_max),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59),
    )
    return (datetime.now(timezone.utc) - delta).strftime("%Y-%m-%d %H:%M:%S")


async def seed():
    print("Initializing database...")
    await init_db()

    async with get_new_db_connection() as conn:
        cursor = await conn.cursor()

        # ── org ──
        await cursor.execute(f"SELECT id FROM {organizations_table_name} WHERE slug = 'sensai-demo' AND deleted_at IS NULL")
        org_row = await cursor.fetchone()
        if org_row:
            org_id = org_row[0]
        else:
            await cursor.execute(
                f"INSERT INTO {organizations_table_name} (slug, name, default_logo_color) VALUES (?, ?, ?)",
                ("sensai-demo", "SensAI Demo School", "#6366f1"),
            )
            org_id = cursor.lastrowid
        print(f"Org ID: {org_id}")

        # ── 1000 users ──
        print("Creating 1000 users...")
        user_ids = []
        for i in range(1000):
            fn = random.choice(FIRST_NAMES)
            ln = random.choice(LAST_NAMES)
            email = f"{fn.lower()}.{ln.lower()}.{i}@sensai-demo.com"
            ts = rand_ts(days_ago_max=120, days_ago_min=1)

            await cursor.execute(f"SELECT id FROM {users_table_name} WHERE email = ?", (email,))
            existing = await cursor.fetchone()
            if existing:
                user_ids.append(existing[0])
            else:
                await cursor.execute(
                    f"INSERT INTO {users_table_name} (email, first_name, last_name, created_at) VALUES (?, ?, ?, ?)",
                    (email, fn, ln, ts),
                )
                user_ids.append(cursor.lastrowid)

            # Link to org
            role = "owner" if i == 0 else ("admin" if i < 5 else "admin")
            await cursor.execute(
                f"INSERT OR IGNORE INTO {user_organizations_table_name} (user_id, org_id, role) VALUES (?, ?, ?)",
                (user_ids[-1], org_id, role),
            )

            # Network profile — first 5 are mentors
            nr = "mentor" if i < 20 else "newbie"
            await cursor.execute(
                f"INSERT OR IGNORE INTO {user_network_profiles_table_name} (user_id, org_id, network_role) VALUES (?, ?, ?)",
                (user_ids[-1], org_id, nr),
            )

        print(f"  {len(user_ids)} users ready")
        await conn.commit()

        # ── cohort + course + tasks (for learning_score) ──
        print("Creating cohort, course, milestones, tasks...")
        await cursor.execute(f"SELECT id FROM {cohorts_table_name} WHERE name = 'Demo Cohort' AND org_id = ? AND deleted_at IS NULL", (org_id,))
        cohort_row = await cursor.fetchone()
        if cohort_row:
            cohort_id = cohort_row[0]
        else:
            await cursor.execute(f"INSERT INTO {cohorts_table_name} (name, org_id) VALUES (?, ?)", ("Demo Cohort", org_id))
            cohort_id = cursor.lastrowid

        # Add all users to cohort
        for uid in user_ids:
            r = "mentor" if uid in user_ids[:20] else "learner"
            await cursor.execute(f"INSERT OR IGNORE INTO {user_cohorts_table_name} (user_id, cohort_id, role) VALUES (?, ?, ?)", (uid, cohort_id, r))

        await cursor.execute(f"SELECT id FROM {courses_table_name} WHERE name = 'DSA Bootcamp' AND org_id = ? AND deleted_at IS NULL", (org_id,))
        course_row = await cursor.fetchone()
        if course_row:
            course_id = course_row[0]
        else:
            await cursor.execute(f"INSERT INTO {courses_table_name} (org_id, name) VALUES (?, ?)", (org_id, "DSA Bootcamp"))
            course_id = cursor.lastrowid

        await cursor.execute(f"INSERT OR IGNORE INTO {course_cohorts_table_name} (course_id, cohort_id) VALUES (?, ?)", (course_id, cohort_id))

        # Create milestone + 50 tasks for task_completions
        await cursor.execute(f"SELECT id FROM {milestones_table_name} WHERE name = 'Fundamentals' AND org_id = ? AND deleted_at IS NULL", (org_id,))
        ms_row = await cursor.fetchone()
        if ms_row:
            milestone_id = ms_row[0]
        else:
            await cursor.execute(f"INSERT INTO {milestones_table_name} (org_id, name, color) VALUES (?, ?, ?)", (org_id, "Fundamentals", "#6366f1"))
            milestone_id = cursor.lastrowid

        await cursor.execute(f"INSERT OR IGNORE INTO {course_milestones_table_name} (course_id, milestone_id, ordering) VALUES (?, ?, ?)", (course_id, milestone_id, 1))

        task_ids = []
        await cursor.execute(f"SELECT id FROM {tasks_table_name} WHERE org_id = ? AND deleted_at IS NULL LIMIT 50", (org_id,))
        existing_tasks = await cursor.fetchall()
        if len(existing_tasks) >= 50:
            task_ids = [r[0] for r in existing_tasks]
        else:
            for t in range(50):
                await cursor.execute(
                    f"INSERT INTO {tasks_table_name} (org_id, type, title, status) VALUES (?, ?, ?, ?)",
                    (org_id, "quiz", f"Task {t+1}: Practice Problem", "published"),
                )
                tid = cursor.lastrowid
                task_ids.append(tid)
                await cursor.execute(
                    f"INSERT OR IGNORE INTO {course_tasks_table_name} (task_id, course_id, milestone_id, ordering) VALUES (?, ?, ?, ?)",
                    (tid, course_id, milestone_id, t + 1),
                )

        # ── task completions (random users complete random tasks) ──
        print("Creating task completions...")
        tc_count = 0
        for uid in user_ids:
            num_completed = random.randint(0, 40)
            completed_tasks = random.sample(task_ids, min(num_completed, len(task_ids)))
            for tid in completed_tasks:
                ts = rand_ts(days_ago_max=60)
                try:
                    await cursor.execute(
                        f"INSERT OR IGNORE INTO {task_completions_table_name} (user_id, task_id, created_at) VALUES (?, ?, ?)",
                        (uid, tid, ts),
                    )
                    tc_count += 1
                except Exception:
                    pass
        print(f"  {tc_count} task completions")
        await conn.commit()

        # ── tags ──
        print("Creating tags...")
        tag_ids = {}
        for tag_name in TAGS:
            slug = tag_name.lower().replace(" ", "-").replace("/", "-")
            await cursor.execute(f"SELECT id FROM {network_tags_table_name} WHERE org_id = ? AND slug = ?", (org_id, slug))
            existing = await cursor.fetchone()
            if existing:
                tag_ids[tag_name] = existing[0]
            else:
                await cursor.execute(f"INSERT INTO {network_tags_table_name} (org_id, name, slug) VALUES (?, ?, ?)", (org_id, tag_name, slug))
                tag_ids[tag_name] = cursor.lastrowid
        print(f"  {len(tag_ids)} tags")
        await conn.commit()

        # ── posts (1200 total: spread across 90 days) ──
        print("Creating 1200 posts across all types...")
        all_tag_names = list(tag_ids.keys())
        post_ids = []
        post_authors = {}

        def make_posts(titles, post_type, count, has_code=False, is_poll=False):
            posts = []
            for i in range(count):
                title = titles[i % len(titles)]
                # Add variation so titles aren't exact dupes
                if count > len(titles):
                    title = f"{title} (#{i // len(titles) + 1})"
                posts.append({"post_type": post_type, "title": title, "has_code": has_code, "is_poll": is_poll})
            return posts

        all_posts = (
            make_posts(THREAD_TITLES, "thread", 200)
            + make_posts(QUESTION_TITLES, "question", 250)
            + make_posts(EXPLANATION_TITLES, "explanation", 250)
            + make_posts(TIP_TITLES, "tip", 200)
            + make_posts(CODE_TITLES, "code_snippet", 200, has_code=True)
            + make_posts(POLL_TITLES, "poll", 100, is_poll=True)
        )
        random.shuffle(all_posts)

        for idx, p in enumerate(all_posts):
            author_id = random.choice(user_ids)
            ts = rand_ts(days_ago_max=90, days_ago_min=0)
            content = random.choice(CONTENT_TEMPLATES)
            code_content = None
            coding_language = None

            if p["has_code"]:
                lang, code = random.choice(CODE_SAMPLES)
                code_content = code
                coding_language = lang

            await cursor.execute(
                f"""INSERT INTO {network_posts_table_name}
                    (org_id, author_id, post_type, title, content_text, code_content, coding_language, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (org_id, author_id, p["post_type"], p["title"], content, code_content, coding_language, ts, ts),
            )
            post_id = cursor.lastrowid
            post_ids.append(post_id)
            post_authors[post_id] = author_id

            # Tags (1-3 per post)
            num_tags = random.randint(1, 3)
            chosen_tags = random.sample(all_tag_names, min(num_tags, len(all_tag_names)))
            for tag_name in chosen_tags:
                tid = tag_ids[tag_name]
                await cursor.execute(f"INSERT OR IGNORE INTO {network_post_tags_table_name} (post_id, tag_id) VALUES (?, ?)", (post_id, tid))
                await cursor.execute(f"UPDATE {network_tags_table_name} SET usage_count = usage_count + 1 WHERE id = ?", (tid,))

            # Poll options
            if p["is_poll"]:
                poll_idx = idx % len(POLL_TITLES)
                options = POLL_OPTIONS_MAP.get(poll_idx, ["Option A", "Option B", "Option C"])
                for opt in options:
                    await cursor.execute(f"INSERT INTO {network_poll_options_table_name} (post_id, option_text) VALUES (?, ?)", (post_id, opt))

            # Update author profile
            await cursor.execute(
                f"UPDATE {user_network_profiles_table_name} SET posts_count = posts_count + 1, last_active_at = ? WHERE user_id = ? AND org_id = ?",
                (ts, author_id, org_id),
            )

            if (idx + 1) % 200 == 0:
                print(f"  {idx + 1} posts created...")
                await conn.commit()

        await conn.commit()
        print(f"  {len(post_ids)} posts total")

        # ── comments (3000+) ──
        print("Creating 3000+ comments...")
        comment_ids = []
        c_count = 0
        for _ in range(3200):
            post_id = random.choice(post_ids)
            commenter_id = random.choice(user_ids)
            template = random.choice(COMMENT_TEMPLATES)
            content = template.replace("{topic}", random.choice(all_tag_names))
            ts = rand_ts(days_ago_max=85, days_ago_min=0)

            code_content = None
            coding_language = None
            if random.random() < 0.15:
                coding_language, code_content = random.choice(CODE_SAMPLES)

            await cursor.execute(
                f"""INSERT INTO {network_comments_table_name}
                    (post_id, author_id, content, code_content, coding_language, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (post_id, commenter_id, content, code_content, coding_language, ts, ts),
            )
            comment_ids.append(cursor.lastrowid)

            await cursor.execute(f"UPDATE {network_posts_table_name} SET reply_count = reply_count + 1 WHERE id = ?", (post_id,))
            await cursor.execute(
                f"UPDATE {user_network_profiles_table_name} SET comments_count = comments_count + 1, last_active_at = ? WHERE user_id = ? AND org_id = ?",
                (ts, commenter_id, org_id),
            )
            c_count += 1
            if c_count % 500 == 0:
                print(f"  {c_count} comments...")
                await conn.commit()

        await conn.commit()
        print(f"  {c_count} comments total")

        # ── post votes (5000+) ──
        print("Creating 5000+ post votes...")
        v_count = 0
        for post_id in post_ids:
            num_voters = random.randint(2, 12)
            voters = random.sample(user_ids, min(num_voters, len(user_ids)))
            for voter_id in voters:
                vote_type = random.choices(["upvote", "downvote"], weights=[88, 12])[0]
                try:
                    await cursor.execute(
                        f"INSERT OR IGNORE INTO {network_votes_table_name} (user_id, target_type, target_id, vote_type, created_at) VALUES (?, ?, ?, ?, ?)",
                        (voter_id, "post", post_id, vote_type, rand_ts(80)),
                    )
                    col = "upvote_count" if vote_type == "upvote" else "downvote_count"
                    await cursor.execute(f"UPDATE {network_posts_table_name} SET {col} = {col} + 1 WHERE id = ?", (post_id,))

                    author_id = post_authors.get(post_id)
                    if author_id:
                        pcol = "upvotes_received" if vote_type == "upvote" else "downvotes_received"
                        await cursor.execute(
                            f"UPDATE {user_network_profiles_table_name} SET {pcol} = {pcol} + 1 WHERE user_id = ? AND org_id = ?",
                            (author_id, org_id),
                        )
                    v_count += 1
                except Exception:
                    pass
            if v_count % 1000 == 0 and v_count > 0:
                await conn.commit()

        await conn.commit()
        print(f"  {v_count} post votes")

        # ── comment votes (2000+) ──
        print("Creating 2000+ comment votes...")
        cv_count = 0
        sampled_comments = random.sample(comment_ids, min(1500, len(comment_ids)))
        for cid in sampled_comments:
            num_voters = random.randint(1, 4)
            voters = random.sample(user_ids, min(num_voters, len(user_ids)))
            for voter_id in voters:
                try:
                    await cursor.execute(
                        f"INSERT OR IGNORE INTO {network_votes_table_name} (user_id, target_type, target_id, vote_type, created_at) VALUES (?, ?, ?, ?, ?)",
                        (voter_id, "comment", cid, "upvote", rand_ts(75)),
                    )
                    await cursor.execute(f"UPDATE {network_comments_table_name} SET upvote_count = upvote_count + 1 WHERE id = ?", (cid,))
                    cv_count += 1
                except Exception:
                    pass
            if cv_count % 500 == 0 and cv_count > 0:
                await conn.commit()

        await conn.commit()
        print(f"  {cv_count} comment votes")

        # ── poll votes ──
        print("Creating poll votes...")
        await cursor.execute(f"SELECT id, post_id FROM {network_poll_options_table_name}")
        all_options = await cursor.fetchall()
        poll_post_options = {}
        for oid, pid in all_options:
            poll_post_options.setdefault(pid, []).append(oid)

        pv_count = 0
        for pid, option_ids in poll_post_options.items():
            voters = random.sample(user_ids, min(random.randint(20, 80), len(user_ids)))
            for voter_id in voters:
                chosen = random.choice(option_ids)
                try:
                    await cursor.execute(
                        f"INSERT OR IGNORE INTO {network_poll_votes_table_name} (user_id, option_id, created_at) VALUES (?, ?, ?)",
                        (voter_id, chosen, rand_ts(60)),
                    )
                    await cursor.execute(f"UPDATE {network_poll_options_table_name} SET vote_count = vote_count + 1 WHERE id = ?", (chosen,))
                    pv_count += 1
                except Exception:
                    pass

        await conn.commit()
        print(f"  {pv_count} poll votes")

    # ── recompute all badges + quality scores ──
    print("Recomputing badges for all users (this may take a minute)...")
    batch_size = 50
    for i in range(0, len(user_ids), batch_size):
        batch = user_ids[i : i + batch_size]
        for uid in batch:
            await recompute_user_badge(uid, org_id)
        if (i + batch_size) % 200 == 0:
            print(f"  {min(i + batch_size, len(user_ids))}/{len(user_ids)} users recomputed...")

    print("Recomputing quality scores for all posts...")
    for i, pid in enumerate(post_ids):
        await recompute_post_quality_score(pid)
        if (i + 1) % 300 == 0:
            print(f"  {i + 1}/{len(post_ids)} posts scored...")

    # ── summary ──
    print("\n=== Seed Summary ===")
    async with get_new_db_connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute(f"SELECT COUNT(*) FROM {users_table_name} WHERE deleted_at IS NULL")
        print(f"Users:           {(await cursor.fetchone())[0]}")
        await cursor.execute(f"SELECT COUNT(*) FROM {network_posts_table_name} WHERE deleted_at IS NULL")
        print(f"Posts:           {(await cursor.fetchone())[0]}")
        await cursor.execute(f"SELECT COUNT(*) FROM {network_comments_table_name} WHERE deleted_at IS NULL")
        print(f"Comments:        {(await cursor.fetchone())[0]}")
        await cursor.execute(f"SELECT COUNT(*) FROM {network_votes_table_name}")
        print(f"Votes:           {(await cursor.fetchone())[0]}")
        await cursor.execute(f"SELECT COUNT(*) FROM {network_poll_votes_table_name}")
        print(f"Poll votes:      {(await cursor.fetchone())[0]}")
        await cursor.execute(f"SELECT COUNT(*) FROM {task_completions_table_name} WHERE deleted_at IS NULL")
        print(f"Task completions:{(await cursor.fetchone())[0]}")

        print("\n=== Top 15 Users by Badge Score ===")
        await cursor.execute(
            f"""SELECT u.first_name, u.last_name, np.badge_tier, np.badge_score, np.network_role,
                    np.learning_score, np.contribution_score, np.posts_count, np.upvotes_received
                FROM {user_network_profiles_table_name} np
                JOIN {users_table_name} u ON np.user_id = u.id
                WHERE np.org_id = ?
                ORDER BY np.badge_score DESC LIMIT 15""",
            (org_id,),
        )
        rows = await cursor.fetchall()
        print(f"{'Name':<22} {'Tier':<14} {'Score':<7} {'Role':<8} {'Learn':<7} {'Contrib':<8} {'Posts':<6} {'Up':<4}")
        print("-" * 80)
        for r in rows:
            print(f"{r[0]+' '+r[1]:<22} {r[2]:<14} {r[3]:<7} {r[4]:<8} {r[5]:<7} {r[6]:<8} {r[7]:<6} {r[8]:<4}")

        print("\n=== Top 5 Trending Tags (last 7 days) ===")
        await cursor.execute(
            f"""SELECT t.name, t.usage_count, COUNT(pt.post_id) as recent
                FROM {network_tags_table_name} t
                JOIN {network_post_tags_table_name} pt ON t.id = pt.tag_id
                JOIN {network_posts_table_name} p ON pt.post_id = p.id
                WHERE t.org_id = ? AND t.deleted_at IS NULL AND p.deleted_at IS NULL
                AND p.created_at >= datetime('now', '-7 days')
                GROUP BY t.id ORDER BY recent DESC, t.usage_count DESC LIMIT 5""",
            (org_id,),
        )
        tag_rows = await cursor.fetchall()
        for r in tag_rows:
            print(f"  {r[0]:<25} total: {r[1]:<5} recent: {r[2]}")

    print(f"\nDone! Database: {sqlite_db_path}")


if __name__ == "__main__":
    asyncio.run(seed())
