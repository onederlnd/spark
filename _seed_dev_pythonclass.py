import random
import os
from datetime import datetime, timedelta, timezone
import bcrypt
from app import create_app
from app.models import get_db

app = create_app()

# =========================================================
# 🔧 GLOBAL CONFIG (EDIT THESE ONLY)
# =========================y===============================

EMOJIS = ["❤️", "💡", "🤔", "🎯", "⚡", "🌟", "🔥"]

FIRST_NAMES = [
    "Alex",
    "Jordan",
    "Taylor",
    "Morgan",
    "Casey",
    "Riley",
    "Avery",
    "Quinn",
    "Cameron",
    "Drew",
    "Reese",
    "Parker",
    "Rowan",
    "Skyler",
    "Emerson",
    "Finley",
    "Hayden",
    "Jules",
    "Kendall",
    "Logan",
]

LAST_NAMES = [
    "Smith",
    "Johnson",
    "Williams",
    "Brown",
    "Jones",
    "Garcia",
    "Miller",
    "Davis",
    "Rodriguez",
    "Martinez",
    "Hernandez",
    "Lopez",
    "Gonzalez",
    "Wilson",
    "Anderson",
    "Thomas",
]

TOPICS = [
    {"name": "Python Basics", "description": "Variables, loops, functions"},
    {"name": "Debugging Help", "description": "Fix code together"},
    {"name": "Project Showcase", "description": "Show what you built"},
    {"name": "Logic & Problem Solving", "description": "Think like a dev"},
    {"name": "Community Chat", "description": "General discussion"},
]

CLASSROOM = {
    "name": "CodeForward - Beginner Python Cohort",
    "description": "Intro to Python for students",
    "join_code": "YXG5WH",
}

POSTS = [
    {
        "user_role": "student",
        "topic": "Python Basics",
        "title": "Why doesn't my loop print?",
        "body": "for i in range(5): print(i) is not working?",
        "replies": [
            {"user_role": "student", "body": "Check indentation"},
            {"user_role": "teacher", "body": "Try putting print on new line"},
        ],
    },
    {
        "user_role": "student",
        "topic": "Debugging Help",
        "title": "Print error",
        "body": 'print(10 % 3 "\\n") crashes',
        "replies": [
            {"user_role": "teacher", "body": "Missing a comma"},
        ],
    },
    {
        "user_role": "student",
        "topic": "Python Basics",
        "title": "What does == mean?",
        "body": "Is == the same as =? I keep getting errors when I use = in my if statement.",
        "replies": [
            {
                "user_role": "teacher",
                "body": "= assigns a value, == checks if two things are equal. Use == in if statements.",
            },
            {
                "user_role": "student",
                "body": "Oh that makes sense! I was using the wrong one.",
            },
        ],
    },
    {
        "user_role": "student",
        "topic": "Python Basics",
        "title": "How do I get user input?",
        "body": "I want my program to ask the user to type something. How do I do that?",
        "replies": [
            {
                "user_role": "teacher",
                "body": "Use input() — for example: name = input('What is your name? ')",
            },
            {"user_role": "student", "body": "That worked! Thank you!"},
        ],
    },
    {
        "user_role": "student",
        "topic": "Debugging Help",
        "title": "NameError: name is not defined",
        "body": "I keep getting NameError on my variable but I already wrote it. What does this mean?",
        "replies": [
            {
                "user_role": "student",
                "body": "Did you spell it the same way? Python is case sensitive.",
            },
            {
                "user_role": "teacher",
                "body": "Also check that you defined it before you used it — order matters.",
            },
        ],
    },
    {
        "user_role": "teacher",
        "topic": "Python Basics",
        "title": "Tip: use print() to debug",
        "body": "When your code isn't working, add print() statements to see what value your variables have at different points. This is called print debugging and it's super useful!",
        "replies": [
            {
                "user_role": "student",
                "body": "I tried this and found my variable was None the whole time!",
            },
            {
                "user_role": "student",
                "body": "This saved me so much time on the calculator assignment.",
            },
        ],
    },
    {
        "user_role": "student",
        "topic": "Project Showcase",
        "title": "I made a number guessing game!",
        "body": "I built a game that picks a random number and tells you if your guess is too high or too low. It loops until you get it right. Really proud of this one!",
        "replies": [
            {
                "user_role": "teacher",
                "body": "Excellent work! Did you use a while loop for the repeat?",
            },
            {"user_role": "student", "body": "Yes! while guess != secret_number"},
            {
                "user_role": "student",
                "body": "That sounds so cool, I want to try making one too.",
            },
        ],
    },
    {
        "user_role": "student",
        "topic": "Logic & Problem Solving",
        "title": "How do I think about breaking down a problem?",
        "body": "When I get a big assignment I don't know where to start. Any advice?",
        "replies": [
            {
                "user_role": "teacher",
                "body": "Start by writing out the steps in plain English before you write any code. This is called pseudocode.",
            },
            {
                "user_role": "student",
                "body": "I do this too! It really helps to just write 'step 1, step 2' first.",
            },
        ],
    },
    {
        "user_role": "student",
        "topic": "Debugging Help",
        "title": "My if/else never runs the else",
        "body": "No matter what I type, my program always runs the if part and skips the else. What am I doing wrong?",
        "replies": [
            {
                "user_role": "teacher",
                "body": "Share your code and we can take a look. Usually it means the condition is always True.",
            },
            {
                "user_role": "student",
                "body": "I bet you accidentally used = instead of == in the condition.",
            },
        ],
    },
    {
        "user_role": "student",
        "topic": "Python Basics",
        "title": "Difference between list and tuple?",
        "body": "We learned about lists and tuples today. They look the same to me. What is the actual difference?",
        "replies": [
            {
                "user_role": "teacher",
                "body": "Lists use [] and can be changed after creation. Tuples use () and cannot be changed. Use tuples when the data should stay fixed.",
            },
            {
                "user_role": "student",
                "body": "So like coordinates would be a tuple since they go together?",
            },
            {"user_role": "teacher", "body": "Exactly right!"},
        ],
    },
    {
        "user_role": "student",
        "topic": "Community Chat",
        "title": "Anyone else find functions confusing at first?",
        "body": "I finally understood functions today after being confused for a week. Anyone else struggle with this?",
        "replies": [
            {
                "user_role": "student",
                "body": "Yes!! I didn't get why you would use them until I had to write the same code three times.",
            },
            {
                "user_role": "student",
                "body": "The moment it clicked for me was when I thought of functions like a recipe.",
            },
            {
                "user_role": "teacher",
                "body": "This is totally normal. Functions are one of those things that suddenly make sense once you need them.",
            },
        ],
    },
    {
        "user_role": "student",
        "topic": "Project Showcase",
        "title": "Made a mad libs program",
        "body": "I built a mad libs game that asks for nouns, verbs, and adjectives then puts them into a silly story. My little sister loved it.",
        "replies": [
            {
                "user_role": "teacher",
                "body": "Love this idea! Great use of input() and string formatting.",
            },
            {
                "user_role": "student",
                "body": "Can you share the code? I want to make one for my family too.",
            },
        ],
    },
    {
        "user_role": "student",
        "topic": "Debugging Help",
        "title": "IndentationError keeps showing up",
        "body": "I get IndentationError but my code looks fine to me. I counted the spaces.",
        "replies": [
            {
                "user_role": "teacher",
                "body": "The most common cause is mixing tabs and spaces. Pick one and stick to it — most editors use 4 spaces.",
            },
            {
                "user_role": "student",
                "body": "I had this problem! Turning on 'show whitespace' in my editor fixed it instantly.",
            },
        ],
    },
    {
        "user_role": "teacher",
        "topic": "Logic & Problem Solving",
        "title": "Challenge: FizzBuzz",
        "body": "Try this classic problem: print numbers 1 to 100. For multiples of 3 print Fizz, for multiples of 5 print Buzz, for both print FizzBuzz. Post your solution!",
        "replies": [
            {
                "user_role": "student",
                "body": "I got it! The key was checking for both before checking each one separately.",
            },
            {
                "user_role": "student",
                "body": "I used the % operator for the first time. Really cool!",
            },
            {
                "user_role": "teacher",
                "body": "Great solutions everyone. Order of the conditions matters a lot here.",
            },
        ],
    },
    {
        "user_role": "student",
        "topic": "Python Basics",
        "title": "How do I add things to a list?",
        "body": "I made a list but I don't know how to add new items to it while the program is running.",
        "replies": [
            {
                "user_role": "teacher",
                "body": "Use .append() — for example: my_list.append('new item')",
            },
            {
                "user_role": "student",
                "body": "There is also .insert() if you want to add it at a specific position.",
            },
        ],
    },
    {
        "user_role": "student",
        "topic": "Community Chat",
        "title": "What got you interested in coding?",
        "body": "I started because I wanted to make a game. What about everyone else?",
        "replies": [
            {
                "user_role": "student",
                "body": "I wanted to automate my homework reminders lol.",
            },
            {
                "user_role": "student",
                "body": "My older brother showed me Python and I thought it was magic.",
            },
            {
                "user_role": "teacher",
                "body": "I started because I wanted to build a website. The first time my code worked I was hooked.",
            },
        ],
    },
    {
        "user_role": "student",
        "topic": "Debugging Help",
        "title": "TypeError: can only concatenate str not int",
        "body": "I'm trying to print a message with a number in it and I get this error. My code is: print('Your score is ' + score)",
        "replies": [
            {
                "user_role": "teacher",
                "body": "You need to convert the number to a string first: print('Your score is ' + str(score))",
            },
            {
                "user_role": "student",
                "body": "Or you can use an f-string: print(f'Your score is {score}') — much easier!",
            },
            {
                "user_role": "teacher",
                "body": "Both work great. F-strings are my personal favorite.",
            },
        ],
    },
    {
        "user_role": "student",
        "topic": "Project Showcase",
        "title": "To-do list app in the terminal",
        "body": "Built a to-do list that lets you add tasks, mark them done, and see everything pending. Used a list and a while loop with a menu.",
        "replies": [
            {
                "user_role": "teacher",
                "body": "This is a great project. Did you figure out how to remove completed items?",
            },
            {"user_role": "student", "body": "I used .remove() for that part."},
            {"user_role": "student", "body": "I want to add this to my portfolio!"},
        ],
    },
    {
        "user_role": "student",
        "topic": "Logic & Problem Solving",
        "title": "What is recursion and when do you use it?",
        "body": "I saw the word recursion in a tutorial and have no idea what it means.",
        "replies": [
            {
                "user_role": "teacher",
                "body": "Recursion is when a function calls itself. A classic example is calculating a factorial. It's a more advanced topic but fun once it clicks!",
            },
            {
                "user_role": "student",
                "body": "My brain hurts just thinking about it but I want to learn it.",
            },
        ],
    },
    {
        "user_role": "student",
        "topic": "Python Basics",
        "title": "What is the difference between return and print?",
        "body": "My function uses print but my teacher said to use return. What is the difference?",
        "replies": [
            {
                "user_role": "teacher",
                "body": "print() shows something on screen but the value disappears after. return sends the value back so you can use it somewhere else in your code.",
            },
            {
                "user_role": "student",
                "body": "Oh so if I want to use the result in a calculation I need return not print.",
            },
            {
                "user_role": "teacher",
                "body": "Exactly! You can always print the returned value separately if you also want to display it.",
            },
        ],
    },
    {
        "user_role": "student",
        "topic": "Community Chat",
        "title": "Finished the calculator assignment early!",
        "body": "Just submitted my calculator with all four operations plus a loop so you can keep calculating without restarting. Feels great to finish early for once.",
        "replies": [
            {
                "user_role": "teacher",
                "body": "Excellent initiative adding the loop — that wasn't required but it makes it much better!",
            },
            {
                "user_role": "student",
                "body": "I need to add that to mine too before the due date.",
            },
        ],
    },
]

ANNOUNCEMENTS = [
    {
        "title": "Welcome to CodeForward!",
        "body": "We're excited to have you here. Start with Python Basics and introduce yourself in Community Chat.",
    },
    {
        "title": "Assignment Reminder",
        "body": "Don't forget — the Calculator assignment is due this Friday!",
    },
    {
        "title": "Live Help Session",
        "body": "I'll be hosting a live debugging session tomorrow at 6pm. Bring your questions!",
    },
    {
        "title": "Great Work So Far",
        "body": "Really impressed with the progress everyone is making. Keep it up!",
    },
]

ASSIGNMENTS = [
    {
        "title": "Build a Calculator",
        "instructions": "Use functions for operations",
        "submission_rate": 1.0,
        "submissions_template": [
            {
                "body": "I built + and -",
                "grade": "A",
                "feedback": "Great work! Consider adding error handling for division by zero.",
            },
        ],
    },
    {
        "title": "FizzBuzz & Beyond",
        "instructions": "Part 1: Write a FizzBuzz program for 1-100. Part 2: Modify it to accept any range and any two divisors as function parameters. Part 3: Add a third divisor and custom word. Your solution must use functions, not just a loop in main.",
        "submission_rate": 0.85,
        "submissions_template": [
            {
                "body": "def fizzbuzz(start, end, d1, w1, d2, w2):\n    for i in range(start, end+1):\n        if i % (d1*d2) == 0:\n            print(w1+w2)\n        elif i % d1 == 0:\n            print(w1)\n        elif i % d2 == 0:\n            print(w2)\n        else:\n            print(i)",
                "grade": "A",
                "feedback": "Excellent — you nailed the parameterized version. The order of conditions is exactly right.",
            },
            {
                "body": "def fizzbuzz(n):\n    for i in range(1, n):\n        if i % 15 == 0:\n            print('FizzBuzz')\n        elif i % 3 == 0:\n            print('Fizz')\n        elif i % 5 == 0:\n            print('Buzz')\n        else:\n            print(i)\nfizzbuzz(100)",
                "grade": "B",
                "feedback": "Good basic implementation but Parts 2 and 3 required parameterized divisors. Hardcoding 15 misses the point of the extension.",
            },
            {
                "body": "for i in range(1, 101):\n    if i % 3 == 0:\n        print('Fizz')\n    elif i % 5 == 0:\n        print('Buzz')\n    else:\n        print(i)",
                "grade": "C",
                "feedback": "This only completes Part 1 and is missing FizzBuzz for multiples of both. Parts 2 and 3 were not attempted. See me during office hours.",
            },
        ],
    },
    {
        "title": "Data Analysis with Lists",
        "instructions": "Given a list of 20 student test scores (you choose the values), write functions to calculate: mean, median, mode, standard deviation, and letter grade distribution. Do not use any imported libraries — implement each calculation yourself. Print a formatted summary report.",
        "submission_rate": 0.65,
        "submissions_template": [
            {
                "body": "scores = [88,92,75,61,90,84,73,95,67,82,79,88,91,55,76,88,94,71,83,69]\n\ndef mean(data):\n    return sum(data) / len(data)\n\ndef median(data):\n    s = sorted(data)\n    n = len(s)\n    return s[n//2] if n % 2 else (s[n//2-1] + s[n//2]) / 2\n\ndef mode(data):\n    counts = {}\n    for x in data:\n        counts[x] = counts.get(x, 0) + 1\n    return max(counts, key=counts.get)\n\nprint(f'Mean: {mean(scores):.2f}')\nprint(f'Median: {median(scores)}')\nprint(f'Mode: {mode(scores)}')",
                "grade": "A",
                "feedback": "Strong work. Mean, median, and mode are all correct. Standard deviation and grade distribution were missing but everything else is clean and well-formatted.",
            },
            {
                "body": "scores = [85, 90, 72, 68, 91, 77, 83, 95, 60, 88]\navg = sum(scores) / len(scores)\nprint('Average:', avg)\nsorted_scores = sorted(scores)\nprint('Median:', sorted_scores[len(sorted_scores)//2])",
                "grade": "C",
                "feedback": "You only implemented mean and a rough median — the median calculation is off for even-length lists. Mode, standard deviation, grade distribution, and the summary report are all missing.",
            },
        ],
    },
    {
        "title": "Text Adventure Game",
        "instructions": "Build a text-based adventure game with at least 5 rooms, a player inventory system, and 3 interactable items. Requirements: use a dictionary to represent rooms with keys for description, exits, and items. The player must be able to pick up items, drop items, and use items. Include a win condition and a lose condition. No external libraries.",
        "submission_rate": 0.55,
        "submissions_template": [
            {
                "body": "rooms = {\n    'entrance': {'desc': 'A dark hallway.', 'exits': {'north': 'library', 'east': 'kitchen'}, 'items': ['torch']},\n    'library': {'desc': 'Walls of dusty books.', 'exits': {'south': 'entrance', 'east': 'study'}, 'items': ['key']},\n    'kitchen': {'desc': 'Smells like something burned.', 'exits': {'west': 'entrance'}, 'items': ['knife']},\n    'study': {'desc': 'A locked chest sits here.', 'exits': {'west': 'library'}, 'items': ['chest']},\n    'cellar': {'desc': 'You found the treasure! You win!', 'exits': {}, 'items': []}\n}\ninventory = []\ncurrent = 'entrance'",
                "grade": "A",
                "feedback": "Really creative world design and your room dictionary structure is exactly right. Inventory system works well. Nice touch adding the lose condition with the knife.",
            },
            {
                "body": "I started building the rooms dictionary and got the movement working between 3 rooms but ran out of time to add inventory. The player can move north/south/east/west and it prints the room description.",
                "grade": "D",
                "feedback": "Movement works but inventory, items, win condition, and lose condition are all missing. Only 3 of 5 required rooms implemented. Please resubmit for partial credit.",
            },
        ],
    },
    {
        "title": "Recursive Algorithms",
        "instructions": "Implement the following using recursion (no loops allowed in the function body): 1) Factorial, 2) Fibonacci sequence, 3) Binary search on a sorted list, 4) Flatten a nested list of arbitrary depth. For each function write at least 3 test cases and explain in comments why recursion is or isn't the best approach for that problem.",
        "submission_rate": 0.35,
        "submissions_template": [
            {
                "body": "def factorial(n):\n    # base case: 0! = 1\n    if n == 0:\n        return 1\n    return n * factorial(n - 1)\n\ndef fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)\n\ndef binary_search(arr, target, low, high):\n    if low > high:\n        return -1\n    mid = (low + high) // 2\n    if arr[mid] == target:\n        return mid\n    elif arr[mid] < target:\n        return binary_search(arr, target, mid+1, high)\n    else:\n        return binary_search(arr, target, low, mid-1)\n\ndef flatten(lst):\n    if not lst:\n        return []\n    if isinstance(lst[0], list):\n        return flatten(lst[0]) + flatten(lst[1:])\n    return [lst[0]] + flatten(lst[1:])",
                "grade": "A",
                "feedback": "All four functions are correct and elegantly written. Your comments on when recursion is appropriate show real understanding. Watch out for Fibonacci performance on large inputs — mention memoization next time.",
            },
            {
                "body": "def factorial(n):\n    if n == 0:\n        return 1\n    return n * factorial(n-1)\n\ndef fibonacci(n):\n    if n == 0: return 0\n    if n == 1: return 1\n    return fibonacci(n-1) + fibonacci(n-2)\n\n# ran out of time for binary search and flatten",
                "grade": "C",
                "feedback": "Factorial and Fibonacci are correct. Binary search and flatten were not submitted — those are half the assignment. No test cases included. Time management needs improvement.",
            },
        ],
    },
    {
        "title": "File I/O & Data Processing",
        "instructions": "Write a program that reads a CSV file of student records (name, grade, subject). Your program must: parse the file without using the csv module, calculate average grade per subject, find the top performer in each subject, write a summary report to a new output file, and handle at least 3 error cases (missing file, malformed rows, empty file) with informative messages. Include a sample CSV with at least 15 rows.",
        "submission_rate": 0.45,
        "submissions_template": [
            {
                "body": "def parse_csv(filename):\n    records = []\n    try:\n        with open(filename, 'r') as f:\n            lines = f.readlines()\n            if not lines:\n                print('Error: file is empty')\n                return []\n            headers = lines[0].strip().split(',')\n            for i, line in enumerate(lines[1:], 2):\n                parts = line.strip().split(',')\n                if len(parts) != 3:\n                    print(f'Warning: skipping malformed row {i}')\n                    continue\n                records.append({'name': parts[0], 'grade': float(parts[1]), 'subject': parts[2]})\n    except FileNotFoundError:\n        print(f'Error: {filename} not found')\n    return records",
                "grade": "A",
                "feedback": "Excellent error handling and clean parsing logic. Average per subject and top performer are both correct. Summary report writes cleanly to file. Best submission in the class.",
            },
            {
                "body": "with open('students.csv') as f:\n    data = f.readlines()\n\nfor line in data[1:]:\n    parts = line.split(',')\n    print(parts[0], parts[1])",
                "grade": "D",
                "feedback": "This only reads and prints the file — no error handling, no averages, no top performer, no output file. No sample CSV included. Please come to office hours before the next assignment.",
            },
        ],
    },
]

QUIZZES = [
    {
        "title": "Quiz: While Loops",
        "instructions": "Test your understanding of while loops in Python. Complete all blocks below.",
        "due_date": "2026-04-25",
        "auto_grade": 1,
        "blocks": [
            {
                "type": "text",
                "position": 0,
                "points": 0,
                "required": 0,
                "body": (
                    "A while loop runs as long as its condition is True. "
                    "Once the condition becomes False, the loop stops.\n\n"
                    "Example:\n"
                    "[code]"
                    "count = 0\n"
                    "while count < 5:\n"
                    "    print(count)\n"
                    "    count += 1[/code]"
                    "This prints 0 through 4, then stops."
                ),
            },
            {
                "type": "multiple_choice",
                "position": 1,
                "points": 2,
                "required": 1,
                "body": "When does a while loop stop running?",
                "choices": [
                    {"body": "After it runs exactly once", "is_correct": 0},
                    {"body": "When its condition becomes False", "is_correct": 1},
                    {"body": "When it reaches the end of the file", "is_correct": 0},
                    {"body": "After a set number of iterations", "is_correct": 0},
                ],
            },
            {
                "type": "true_false",
                "position": 2,
                "points": 1,
                "required": 1,
                "body": "True or False: A while loop can run zero times if the condition is False before it starts.",
                "choices": [
                    {"body": "True", "is_correct": 1},
                    {"body": "False", "is_correct": 0},
                ],
            },
            {
                "type": "code",
                "position": 3,
                "points": 5,
                "required": 1,
                "body": (
                    "Write a while loop that counts down from 10 to 1 and prints each number. "
                    "On the last iteration, also print 'Blastoff!'."
                ),
            },
            {
                "type": "short_answer",
                "position": 4,
                "points": 3,
                "required": 1,
                "body": (
                    "In your own words, what is an infinite loop? "
                    "Give one example of how you could accidentally create one."
                ),
            },
        ],
        "submission_rate": 0.85,
        "submissions_template": [
            {
                "grade": "A",
                "feedback": "Great work! Clean countdown and correct blastoff placement.",
                "block_responses": [
                    {"position": 0, "body": None, "score": 0},
                    {"position": 1, "choice_index": 1, "score": 2},
                    {"position": 2, "choice_index": 0, "score": 1},
                    {
                        "position": 3,
                        "body": (
                            "i = 10\n"
                            "while i >= 1:\n"
                            "    if i == 1:\n"
                            "        print(i)\n"
                            "        print('Blastoff!')\n"
                            "    else:\n"
                            "        print(i)\n"
                            "    i -= 1"
                        ),
                        "score": 5,
                    },
                    {
                        "position": 4,
                        "body": (
                            "An infinite loop is a loop that never stops because its condition "
                            "never becomes False. You could accidentally create one by forgetting "
                            "to update the variable in the condition, like writing while count < 5 "
                            "but never incrementing count."
                        ),
                        "score": 3,
                    },
                ],
            },
            {
                "grade": "B",
                "feedback": "Countdown works but Blastoff printed outside the loop.",
                "block_responses": [
                    {"position": 0, "body": None, "score": 0},
                    {"position": 1, "choice_index": 1, "score": 2},
                    {"position": 2, "choice_index": 1, "score": 0},
                    {
                        "position": 3,
                        "body": (
                            "i = 10\n"
                            "while i > 0:\n"
                            "    print(i)\n"
                            "    i -= 1\n"
                            "print('Blastoff!')"
                        ),
                        "score": 3,
                    },
                    {
                        "position": 4,
                        "body": "An infinite loop runs forever. Like if you forget to change i.",
                        "score": 2,
                    },
                ],
            },
            {
                "grade": "C",
                "feedback": "Loop counts down but never prints Blastoff. Short answer too brief.",
                "block_responses": [
                    {"position": 0, "body": None, "score": 0},
                    {"position": 1, "choice_index": 2, "score": 0},
                    {"position": 2, "choice_index": 1, "score": 0},
                    {
                        "position": 3,
                        "body": ("i = 10\nwhile i > 0:\n    print(i)\n    i -= 1"),
                        "score": 2,
                    },
                    {
                        "position": 4,
                        "body": "A loop that doesn't stop.",
                        "score": 1,
                    },
                ],
            },
        ],
    },
    {
        "title": "Quiz: Lists & Indexing",
        "instructions": "Test your understanding of Python lists and how to access items by index. Complete all blocks below.",
        "due_date": "2026-05-02",
        "auto_grade": 1,
        "blocks": [
            {
                "type": "text",
                "position": 0,
                "points": 0,
                "required": 0,
                "body": (
                    "A list is an ordered collection of items. You access items using an index, "
                    "starting at 0 for the first item.\n\n"
                    "Example:\n"
                    "[code] fruits = ['apple', 'banana', 'cherry']\n"
                    "print(fruits[0])  # apple\n"
                    "print(fruits[2])  # cherry\n"
                    "print(fruits[-1]) # cherry (negative index counts from the end)"
                    "[/code]"
                    "Lists can hold any data type and can be changed after creation."
                ),
            },
            {
                "type": "multiple_choice",
                "position": 1,
                "points": 2,
                "required": 1,
                "body": (
                    "Given: colors = ['red', 'green', 'blue']\n"
                    "What does colors[1] return?"
                ),
                "choices": [
                    {"body": "'red'", "is_correct": 0},
                    {"body": "'green'", "is_correct": 1},
                    {"body": "'blue'", "is_correct": 0},
                    {"body": "An IndexError", "is_correct": 0},
                ],
            },
            {
                "type": "true_false",
                "position": 2,
                "points": 1,
                "required": 1,
                "body": "True or False: In Python, list indexing starts at 1.",
                "choices": [
                    {"body": "True", "is_correct": 0},
                    {"body": "False", "is_correct": 1},
                ],
            },
            {
                "type": "multiple_choice",
                "position": 3,
                "points": 2,
                "required": 1,
                "body": (
                    "Given: nums = [10, 20, 30, 40, 50]\nWhat does nums[-1] return?"
                ),
                "choices": [
                    {"body": "10", "is_correct": 0},
                    {"body": "40", "is_correct": 0},
                    {"body": "50", "is_correct": 1},
                    {"body": "An IndexError", "is_correct": 0},
                ],
            },
            {
                "type": "code",
                "position": 4,
                "points": 5,
                "required": 1,
                "body": (
                    "Create a list called 'animals' containing at least 4 animal names. "
                    "Then, using indexing, print the first item, the last item, and the second item."
                ),
            },
            {
                "type": "short_answer",
                "position": 5,
                "points": 3,
                "required": 1,
                "body": (
                    "What happens when you try to access an index that doesn't exist in a list? "
                    "Give an example and explain the error you would see."
                ),
            },
        ],
        "submission_rate": 0.80,
        "submissions_template": [
            {
                "grade": "A",
                "feedback": "Excellent! Correct indexing throughout and a thorough short answer.",
                "block_responses": [
                    {"position": 0, "body": None, "score": 0},
                    {"position": 1, "choice_index": 1, "score": 2},
                    {"position": 2, "choice_index": 1, "score": 1},
                    {"position": 3, "choice_index": 2, "score": 2},
                    {
                        "position": 4,
                        "body": (
                            "animals = ['dog', 'cat', 'elephant', 'parrot']\n"
                            "print(animals[0])   # dog\n"
                            "print(animals[-1])  # parrot\n"
                            "print(animals[1])   # cat"
                        ),
                        "score": 5,
                    },
                    {
                        "position": 5,
                        "body": (
                            "If you access an index that doesn't exist, Python raises an IndexError. "
                            "For example, if my_list = [1, 2, 3] and I write my_list[5], Python will "
                            "say 'IndexError: list index out of range' because there is no item at index 5."
                        ),
                        "score": 3,
                    },
                ],
            },
            {
                "grade": "B",
                "feedback": "Good work on indexing. Short answer explanation could be more detailed.",
                "block_responses": [
                    {"position": 0, "body": None, "score": 0},
                    {"position": 1, "choice_index": 1, "score": 2},
                    {"position": 2, "choice_index": 1, "score": 1},
                    {"position": 3, "choice_index": 2, "score": 2},
                    {
                        "position": 4,
                        "body": (
                            "animals = ['lion', 'tiger', 'bear', 'wolf']\n"
                            "print(animals[0])\n"
                            "print(animals[3])\n"
                            "print(animals[1])"
                        ),
                        "score": 4,
                    },
                    {
                        "position": 5,
                        "body": "You get an IndexError. Like if you do list[10] but it only has 3 items.",
                        "score": 2,
                    },
                ],
            },
            {
                "grade": "C",
                "feedback": "Mixed up indexing in the code block. Review how index positions work.",
                "block_responses": [
                    {"position": 0, "body": None, "score": 0},
                    {"position": 1, "choice_index": 0, "score": 0},
                    {"position": 2, "choice_index": 0, "score": 0},
                    {"position": 3, "choice_index": 1, "score": 0},
                    {
                        "position": 4,
                        "body": (
                            "animals = ['fish', 'bird', 'frog', 'snake']\n"
                            "print(animals[1])\n"
                            "print(animals[4])\n"
                            "print(animals[2])"
                        ),
                        "score": 2,
                    },
                    {
                        "position": 5,
                        "body": "It crashes.",
                        "score": 1,
                    },
                ],
            },
        ],
    },
]

FILTERED_WORDS = ["stupid", "hate"]

BUG_REPORTS = [
    {
        "user_role": "student",
        "title": "Post button not working",
        "description": "Sometimes clicking post does nothing",
        "severity": "medium",
    }
]

# Conversations to seed. Each entry creates one conversation.
CONVERSATIONS = [
    # --- DMs: student <-> teacher ---
    {
        "type": "dm",
        "participants": ["student", "teacher"],
        "messages": [
            {
                "role": "student",
                "body": "Hey, I'm stuck on the FizzBuzz assignment — can you help?",
            },
            {"role": "teacher", "body": "Of course! Where are you getting stuck?"},
            {
                "role": "student",
                "body": "I don't know how to check for both 3 and 5 at the same time.",
            },
            {
                "role": "teacher",
                "body": "Try checking i % 15 == 0 first, before the individual checks.",
            },
            {"role": "student", "body": "Oh that worked! Thank you so much!"},
        ],
    },
    {
        "type": "dm",
        "participants": ["student", "teacher"],
        "messages": [
            {
                "role": "teacher",
                "body": "Just wanted to check in — how is the text adventure going?",
            },
            {
                "role": "student",
                "body": "Pretty good! I have 4 rooms done, just need one more.",
            },
            {
                "role": "teacher",
                "body": "Great progress! Don't forget the win/lose conditions.",
            },
        ],
    },
    {
        "type": "dm",
        "participants": ["student", "teacher"],
        "messages": [
            {
                "role": "student",
                "body": "Can I get an extension on the File I/O assignment?",
            },
            {
                "role": "teacher",
                "body": "I can give you one extra day. Submit by tomorrow night.",
            },
            {"role": "student", "body": "Thank you, I really appreciate it!"},
        ],
    },
    # --- Group conversations ---
    {
        "type": "group",
        "title": "FizzBuzz Study Group",
        "participant_roles": ["student", "student", "student", "teacher"],
        "messages": [
            {
                "role": "student",
                "body": "Anyone else confused about Part 2 of the FizzBuzz assignment?",
            },
            {
                "role": "student",
                "body": "Yeah I have no idea how to make the divisors a parameter.",
            },
            {
                "role": "teacher",
                "body": "Think about it like this — instead of hardcoding 3 and 5, what if your function accepted them as arguments?",
            },
            {"role": "student", "body": "Ohhhh so like def fizzbuzz(d1, d2)?"},
            {"role": "teacher", "body": "Exactly! Give it a try."},
            {"role": "student", "body": "Got it working! This is way cleaner."},
        ],
    },
    {
        "type": "group",
        "title": "Project Showcase Planning",
        "participant_roles": ["student", "student", "student"],
        "messages": [
            {
                "role": "student",
                "body": "Should we do a group demo day for our projects?",
            },
            {
                "role": "student",
                "body": "That would be so fun, I want to show my mad libs game.",
            },
            {
                "role": "student",
                "body": "I'll ask the teacher if we can do it next week.",
            },
        ],
    },
    # --- Under-13 COPPA conversation (for oversight testing) ---
    {
        "type": "dm",
        "participants": ["student", "teacher"],
        "coppa": True,  # marks the student as under 13
        "messages": [
            {
                "role": "student",
                "body": "I don't understand the recursion assignment at all.",
            },
            {
                "role": "teacher",
                "body": "No worries! Let's go through factorial together. What does factorial(3) mean to you?",
            },
            {"role": "student", "body": "Um… 3 times 2 times 1?"},
            {
                "role": "teacher",
                "body": "Exactly! Now imagine writing a function that calls itself with n-1 each time. Try writing that out.",
            },
        ],
    },
]


# =========================================================
# 👥 USER GENERATION
# =========================================================


def generate_username(first, last, existing):
    base = f"{first.lower()}.{last.lower()}"
    if base not in existing:
        return base
    i = 1
    while True:
        username = f"{base}.{i:02d}"
        if username not in existing:
            return username
        i += 1


def generate_users():
    users = []
    used = set()

    for i, (first, last) in enumerate(zip(FIRST_NAMES, LAST_NAMES)):
        role = "teacher" if i < 2 else "student"
        username = generate_username(first, last, used)
        used.add(username)
        users.append(
            {
                "username": username,
                "role": role,
                "display_name": f"{first} {last}",
            }
        )

    users.append(
        {
            "username": "parent.demo",
            "role": "parent",
            "display_name": "Demo Parent",
        }
    )

    return users


USERS = generate_users()

# =========================================================
# 🧠 HELPERS
# =========================================================


def now():
    """Return current UTC time as a string, timezone-aware."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def days_ago(days):
    """Return UTC datetime string for N days ago, timezone-aware."""
    return (datetime.now(timezone.utc) - timedelta(days=days)).strftime(
        "%Y-%m-%d %H:%M:%S"
    )


def insert_and_get_id(db, query, params):
    return db.execute(query, params).lastrowid


def pick_user(users, role):
    pool = [u for u in users.values() if u["role"] == role]
    return random.choice(pool)["id"]


def clear_db(db):
    """
    Drops all user-created tables to reset the database.
    """
    tables = db.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
    for t in tables:
        name = t["name"]
        if name.startswith("sqlite_"):
            continue
        db.execute(f"DROP TABLE IF EXISTS {name}")
    db.commit()
    print("🧹 Database cleared!")


# =========================================================
# 🌱 SEED FUNCTIONS
# =========================================================


def seed_admin(db):
    username = os.environ.get("ADMIN_USERNAME")
    password = os.environ.get("ADMIN_PASSWORD")
    role = os.environ.get("ADMIN_ROLE", "teacher")
    display_name = os.environ.get("ADMIN_DISPLAY_NAME")
    db.execute(
        """
        INSERT OR IGNORE INTO users
        (username, password_hash, role, display_name, bio, dob, coppa_status, onboarded, tour_seen)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            username,
            bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode(),
            role,
            display_name,
            "",
            "2000-01-01",
            "approved",
            0,
            0,
        ),
    )


def seed_users(db):
    users = {}

    for u in USERS:
        db.execute(
            """
            INSERT OR IGNORE INTO users
            (username, password_hash, role, display_name, bio, dob, coppa_status, onboarded, tour_seen)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                u["username"],
                bcrypt.hashpw("pass123".encode(), bcrypt.gensalt()).decode(),
                u["role"],
                u["display_name"],
                f"{u['role']} in Python program",
                "2000-01-01",
                "approved",
                1,
                0,
            ),
        )

    rows = db.execute("SELECT id, username, role FROM users").fetchall()

    for r in rows:
        users[r["username"]] = {"id": r["id"], "role": r["role"]}

    return users


def seed_topics(db):
    ids = {}
    for t in TOPICS:
        db.execute(
            "INSERT OR IGNORE INTO topics (name, description) VALUES (?, ?)",
            (t["name"], t["description"]),
        )

    rows = db.execute("SELECT id, name FROM topics").fetchall()
    for r in rows:
        ids[r["name"]] = r["id"]

    return ids


def seed_classroom(db, users):
    teacher_id = pick_user(users, "teacher")

    classroom_id = insert_and_get_id(
        db,
        """
        INSERT INTO classrooms (teacher_id, name, description, join_code)
        VALUES (?, ?, ?, ?)
        """,
        (
            teacher_id,
            CLASSROOM["name"],
            CLASSROOM["description"],
            CLASSROOM["join_code"],
        ),
    )

    for u in users.values():
        if u["role"] in ["student", "teacher"]:
            db.execute(
                """
                INSERT OR IGNORE INTO classroom_members (classroom_id, user_id, role)
                VALUES (?, ?, ?)
                """,
                (classroom_id, u["id"], u["role"]),
            )

    admin = db.execute(
        "SELECT id FROM users WHERE username = ?", (os.environ.get("ADMIN_USERNAME"),)
    ).fetchone()
    if admin:
        db.execute(
            "INSERT OR IGNORE INTO classroom_members (classroom_id, user_id, role) VALUES (?, ?, ?)",
            (classroom_id, admin["id"], "teacher"),
        )

    return classroom_id


def seed_posts(db, users, topics, classroom_id):
    post_ids = []

    for p in POSTS:
        uid = (
            users[p["user"]]["id"] if "user" in p else pick_user(users, p["user_role"])
        )

        pid = insert_and_get_id(
            db,
            """
            INSERT INTO posts (user_id, topic_id, title, body, classroom_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                uid,
                topics[p["topic"]],
                p["title"],
                p["body"],
                classroom_id,
                days_ago(random.randint(0, 3)),
            ),
        )

        post_ids.append(pid)

        for r in p.get("replies", []):
            rid = (
                users[r["user"]]["id"]
                if "user" in r
                else pick_user(users, r["user_role"])
            )

            insert_and_get_id(
                db,
                """
                INSERT INTO posts (user_id, body, parent_id, classroom_id, title, created_at)
                VALUES (?, ?, ?, ?, '', ?)
                """,
                (rid, r["body"], pid, classroom_id, now()),
            )

            db.execute(
                "UPDATE posts SET reply_count = reply_count + 1 WHERE id = ?", (pid,)
            )

    return post_ids


def seed_announcements(db, users, classroom_id):
    teacher_ids = [u["id"] for u in users.values() if u["role"] == "teacher"]

    for a in ANNOUNCEMENTS:
        insert_and_get_id(
            db,
            """
            INSERT INTO posts (
                post_type, user_id, title, body, classroom_id, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "announcement",
                random.choice(teacher_ids),
                a["title"],
                a["body"],
                classroom_id,
                days_ago(random.randint(0, 5)),
            ),
        )


def seed_reactions(db, users, post_ids):
    for pid in post_ids:
        for u in users.values():
            if random.random() < 0.4:
                db.execute(
                    """
                    INSERT OR IGNORE INTO reactions (post_id, user_id, reaction, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (pid, u["id"], random.choice(EMOJIS), now()),
                )


def seed_assignments(db, users, classroom_id):
    students = [u for u in users.values() if u["role"] == "student"]

    for a in ASSIGNMENTS:
        aid = insert_and_get_id(
            db,
            """
            INSERT INTO assignments (classroom_id, title, instructions)
            VALUES (?, ?, ?)
            """,
            (classroom_id, a["title"], a["instructions"]),
        )

        rate = a.get("submission_rate", 1.0)
        templates = a.get("submissions_template", [])
        if not templates:
            continue

        submitting_students = [s for s in students if random.random() < rate]

        for student in submitting_students:
            template = random.choice(templates)
            db.execute(
                """
                INSERT OR IGNORE INTO submissions (assignment_id, user_id, body, grade, feedback)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    aid,
                    student["id"],
                    template["body"],
                    template.get("grade"),
                    template.get("feedback"),
                ),
            )


def seed_quiz_assignment(db, users, classroom_id):
    students = [u for u in users.values() if u["role"] == "student"]

    for q in QUIZZES:
        qid = insert_and_get_id(
            db,
            """
            INSERT INTO assignments (classroom_id, title, instructions)
            VALUES (?,?,?)
            """,
            (classroom_id, q["title"], q["instructions"]),
        )

        block_ids = {}
        block_choice_ids = {}

        for block in q.get("blocks", []):
            bid = insert_and_get_id(
                db,
                """
                INSERT INTO lesson_blocks (assignment_id, type, body, position, points, required)
                VALUES (?,?,?,?,?,?)
                """,
                (
                    qid,
                    block["type"],
                    block["body"],
                    block["position"],
                    block["points"],
                    block.get("required", 1),
                ),
            )
            block_ids[block["position"]] = bid

            if "choices" in block:
                ids = []
                for choice in block["choices"]:
                    cid = insert_and_get_id(
                        db,
                        "INSERT INTO block_choices (block_id, body, is_correct) VALUES (?,?,?)",
                        (bid, choice["body"], choice["is_correct"]),
                    )
                    ids.append(cid)
                block_choice_ids[block["position"]] = ids

        rate = q.get("submission_rate", 1.0)
        templates = q.get("submissions_template", [])
        if not templates:
            continue

        submitting_students = [s for s in students if random.random() < rate]

        for student in submitting_students:
            template = random.choice(templates)
            sub_id = insert_and_get_id(
                db,
                """
                INSERT OR IGNORE INTO submissions (assignment_id, user_id, body, grade, feedback)
                VALUES (?,?,?,?,?)
                """,
                (
                    qid,
                    student["id"],
                    "",
                    template.get("grade"),
                    template.get("feedback"),
                ),
            )

            for resp in template.get("block_responses", []):
                if resp["position"] == 0:
                    continue

                choice_id = None
                if "choice_index" in resp:
                    choice_id = block_choice_ids[resp["position"]][resp["choice_index"]]

                db.execute(
                    """
                    INSERT INTO block_responses (submission_id, block_id, choice_id, body, score)
                    VALUES (?,?,?,?,?)
                    """,
                    (
                        sub_id,
                        block_ids[resp["position"]],
                        choice_id,
                        resp.get("body"),
                        resp.get("score", 0),
                    ),
                )


def seed_filtered_words(db):
    for word in FILTERED_WORDS:
        db.execute("INSERT OR IGNORE INTO filtered_words (word) VALUES (?)", (word,))


def seed_bug_reports(db, users):
    for b in BUG_REPORTS:
        uid = (
            users[b["user"]]["id"] if "user" in b else pick_user(users, b["user_role"])
        )

        db.execute(
            """
            INSERT INTO bug_reports (reported_by, title, description, severity)
            VALUES (?, ?, ?, ?)
            """,
            (uid, b["title"], b["description"], b["severity"]),
        )


def seed_conversations(db, users, classroom_id):
    from app.models.messaging import get_or_create_dm, create_conversation, send_message

    students = [u for u in users.values() if u["role"] == "student"]
    teachers = [u for u in users.values() if u["role"] == "teacher"]

    used_dm_pairs = set()

    for conv in CONVERSATIONS:
        is_coppa = conv.get("coppa", False)

        if conv["type"] == "dm":
            # Pick a unique student/teacher pair
            student = None
            for s in random.sample(students, len(students)):
                for t in random.sample(teachers, len(teachers)):
                    pair = (s["id"], t["id"])
                    if pair not in used_dm_pairs:
                        student, teacher = s, t
                        used_dm_pairs.add(pair)
                        break
                if student:
                    break

            if not student:
                continue

            # Mark student as under-13 for COPPA test conversations
            if is_coppa:
                from datetime import date

                dob = date(date.today().year - 11, 6, 15).isoformat()
                db.execute(
                    "UPDATE users SET dob = ?, coppa_status = 'pending' WHERE id = ?",
                    (dob, student["id"]),
                )

            conv_id = get_or_create_dm(classroom_id, student["id"], teacher["id"])
            role_map = {"student": student["id"], "teacher": teacher["id"]}

        else:  # group
            participant_roles = conv.get(
                "participant_roles", ["student", "student", "teacher"]
            )
            available_students = random.sample(
                students, min(len(students), participant_roles.count("student"))
            )
            available_teachers = random.sample(
                teachers, min(len(teachers), participant_roles.count("teacher"))
            )

            members = []
            si, ti = 0, 0
            for role in participant_roles:
                if role == "student" and si < len(available_students):
                    members.append(available_students[si])
                    si += 1
                elif role == "teacher" and ti < len(available_teachers):
                    members.append(available_teachers[ti])
                    ti += 1

            if len(members) < 2:
                continue

            member_ids = [m["id"] for m in members]
            conv_id = create_conversation(
                classroom_id, member_ids[0], member_ids[1:], title=conv.get("title")
            )
            role_map = {
                "student": [m["id"] for m in members if m["role"] == "student"],
                "teacher": [m["id"] for m in members if m["role"] == "teacher"],
            }

        # Insert messages
        student_idx = teacher_idx = 0
        for msg in conv.get("messages", []):
            if conv["type"] == "dm":
                sender_id = role_map[msg["role"]]
            else:
                pool = role_map[msg["role"]]
                if msg["role"] == "student":
                    sender_id = pool[student_idx % len(pool)]
                    student_idx += 1
                else:
                    sender_id = pool[teacher_idx % len(pool)]
                    teacher_idx += 1

            send_message(conv_id, sender_id, msg["body"])


# =========================================================
# 🚀 MAIN
# =========================================================


def main():
    with app.app_context():
        db = get_db()

        # Clear everything first
        clear_db(db)

        from app.models import init_db

        init_db(app)
        seed_admin(db)
        users = seed_users(db)
        topics = seed_topics(db)
        classroom_id = seed_classroom(db, users)

        seed_announcements(db, users, classroom_id)
        post_ids = seed_posts(db, users, topics, classroom_id)
        seed_reactions(db, users, post_ids)
        seed_assignments(db, users, classroom_id)
        seed_quiz_assignment(db, users, classroom_id)
        seed_filtered_words(db)
        seed_bug_reports(db, users)
        seed_conversations(db, users, classroom_id)
        db.commit()

        print("✅ Demo seed complete!")

        # -------------------------------
        # Print usernames with password
        # -------------------------------

    # -------------------------------
    # Print usernames by role with password
    # -------------------------------
    print("\n📝 Users & Demo Passwords:")

    teachers = [u for u in USERS if u["role"] == "teacher"]
    students = [u for u in USERS if u["role"] == "student"]

    print("\n👩‍ Admin:")
    print("Admin account seeded")

    print("\n👩‍🏫 Teachers:")
    for t in teachers:
        print(
            f"Username: {t['username']:<20} | Role: {t['role']:<7} | Password: pass123"
        )

    print("\n🧑‍🎓 Students:")
    for s in students:
        print(
            f"Username: {s['username']:<20} | Role: {s['role']:<7} | Password: pass123"
        )


if __name__ == "__main__":
    main()
