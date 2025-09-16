#!/usr/bin/env python3
"""
Smart Attendance System - Git Branch Management Dashboard

This script provides a visual overview of your Git branch status,
aligned with your 4-sprint Agile Scrum methodology for the
Smart Attendance System project.

Features:
- Visual sprint-based branch organization
- Color-coded branch status (merged, pending, active)
- Sprint progress tracking
- Actionable recommendations
- Interactive mode for common Git operations
- Compliance with your branch naming convention

Usage:
  python branch_dashboard.py [options]

Options:
  --refresh    Refresh branch data from Git
  --interactive  Enter interactive mode
  --help       Show this help message
"""

import os
import sys
import subprocess
import json
import re
from datetime import datetime, timedelta
from collections import defaultdict
import shutil

# Configuration - Match your project structure
SPRINT_CONFIG = {
    1: {
        "name": "Setup & Registration",
        "dates": "Day 1-10",
        "branches": [
            "feature/001-setup",
            "feature/002-registration-ui",
            "feature/003-face-capture",
            "feature/004-db-storage",
            "feature/004a-uuid-migration",
            "feature/004b-256d-vectors",
            "feature/004c-encryption"
        ]
    },
    2: {
        "name": "Real-Time Recognition",
        "dates": "Day 11-20",
        "branches": [
            "feature/005-video-stream",
            "feature/006-face-matching",
            "feature/006a-openvino-integration",
            "feature/006b-threshold-calibration",
            "feature/007-attendance-logging",
            "feature/007a-liveness-detection",
            "feature/007b-attendance-status"
        ]
    },
    3: {
        "name": "Dashboard & Export",
        "dates": "Day 21-30",
        "branches": [
            "feature/008-dashboard-ui",
            "feature/009-live-updates",
            "feature/010-export-csv-pdf",
            "feature/010a-report-templates",
            "feature/010b-export-validation"
        ]
    },
    4: {
        "name": "Alerts & Polish",
        "dates": "Day 31-40",
        "branches": [
            "feature/011-alerts",
            "feature/011a-email-integration",
            "feature/011b-sms-integration",
            "feature/012-unknown-detection",
            "feature/012a-security-logs",
            "feature/013-manual-override",
            "feature/014-testing-docs",
            "feature/014a-unit-tests",
            "feature/014b-integration-tests",
            "feature/014c-compliance-docs"
        ]
    }
}

# Color definitions for terminal output
COLORS = {
    'HEADER': '\033[95m',
    'OKBLUE': '\033[94m',
    'OKCYAN': '\033[96m',
    'OKGREEN': '\033[92m',
    'WARNING': '\033[93m',
    'FAIL': '\033[91m',
    'ENDC': '\033[0m',
    'BOLD': '\033[1m',
    'UNDERLINE': '\033[4m',
    'MERGED': '\033[92m',
    'PENDING': '\033[93m',
    'ACTIVE': '\033[94m',
    'MISSING': '\033[91m',
    'HOTFIX': '\033[1;91m',
    'RELEASE': '\033[1;95m',
    'SECURITY': '\033[1;96m',
    'TEST': '\033[1;93m',
}

def check_git_repo():
    """Check if current directory is a Git repository"""
    try:
        subprocess.check_output(['git', 'rev-parse', '--is-inside-work-tree'])
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def get_branch_data(refresh=False):
    """
    Get branch data from Git repository
    
    Returns:
        {
            'all_branches': list of all branches,
            'active_branch': current branch,
            'sprint_branches': {
                sprint_number: {
                    'planned': list of planned branches,
                    'exists': list of existing branches,
                    'merged': list of merged branches,
                    'pending': list of pending branches
                }
            },
            'release_branches': list of release branches,
            'hotfix_branches': list of hotfix branches,
            'security_branches': list of security branches,
            'test_branches': list of test branches
        }
    """
    # Check if we're in a Git repo
    if not check_git_repo():
        print(f"{COLORS['FAIL']}Error: Not in a Git repository{COLORS['ENDC']}")
        sys.exit(1)
    
    # Get all branches
    branches = subprocess.check_output(
        ['git', 'branch', '-a'], 
        universal_newlines=True
    ).splitlines()
    
    # Clean branch names
    all_branches = []
    active_branch = None
    for branch in branches:
        branch = branch.strip()
        if branch.startswith('*'):
            active_branch = branch[2:].replace('remotes/origin/', '').strip()
        branch = branch.replace('*', '').strip().replace('remotes/origin/', '')
        if branch and 'HEAD' not in branch:
            all_branches.append(branch)
    
    # Initialize data structure
    data = {
        'all_branches': all_branches,
        'active_branch': active_branch,
        'sprint_branches': {},
        'release_branches': [],
        'hotfix_branches': [],
        'security_branches': [],
        'test_branches': [],
        'calibration_branches': []
    }
    
    # Categorize branches by sprint
    for sprint_num, config in SPRINT_CONFIG.items():
        planned = config['branches']
        exists = []
        merged = []
        pending = []
        
        for branch in all_branches:
            # Check if branch belongs to this sprint
            if any(branch == planned_branch for planned_branch in planned):
                exists.append(branch)
                
                # Check if merged into develop
                try:
                    subprocess.check_output(
                        ['git', 'branch', '--contains', branch, 'develop'],
                        stderr=subprocess.DEVNULL
                    )
                    merged.append(branch)
                except subprocess.CalledProcessError:
                    pending.append(branch)
        
        # Sort branches for consistent display
        exists.sort()
        merged.sort()
        pending.sort()
        
        data['sprint_branches'][sprint_num] = {
            'planned': planned,
            'exists': exists,
            'merged': merged,
            'pending': pending
        }
    
    # Categorize special branches
    for branch in all_branches:
        if branch.startswith('release/'):
            data['release_branches'].append(branch)
        elif branch.startswith('hotfix/'):
            data['hotfix_branches'].append(branch)
        elif branch.startswith('security/'):
            data['security_branches'].append(branch)
        elif branch.startswith('test/'):
            data['test_branches'].append(branch)
        elif branch.startswith('calibration/'):
            data['calibration_branches'].append(branch)
    
    return data

def get_sprint_status(data):
    """Calculate sprint status based on branch progress"""
    sprint_status = {}
    
    for sprint_num in SPRINT_CONFIG.keys():
        sprint_data = data['sprint_branches'][sprint_num]
        planned_count = len(sprint_data['planned'])
        merged_count = len(sprint_data['merged'])
        pending_count = len(sprint_data['pending'])
        
        # Calculate progress percentage
        if planned_count > 0:
            progress = (merged_count / planned_count) * 100
        else:
            progress = 100  # No branches planned = 100% complete
        
        # Determine status
        if progress >= 100:
            status = "Completed"
        elif progress >= 75:
            status = "On Track"
        elif progress >= 50:
            status = "Needs Attention"
        else:
            status = "At Risk"
        
        sprint_status[sprint_num] = {
            'progress': progress,
            'status': status,
            'merged': merged_count,
            'pending': pending_count,
            'total': planned_count
        }
    
    return sprint_status

def draw_progress_bar(percentage, width=30):
    """Draw a progress bar with color coding"""
    filled = int(width * percentage / 100)
    empty = width - filled
    
    if percentage >= 90:
        color = COLORS['OKGREEN']
    elif percentage >= 70:
        color = COLORS['OKCYAN']
    elif percentage >= 50:
        color = COLORS['WARNING']
    else:
        color = COLORS['FAIL']
    
    return f"[{color}{'█' * filled}{COLORS['ENDC']}{' ' * empty}] {int(percentage)}%"

def display_dashboard(data):
    """Display the branch management dashboard"""
    # Clear screen for clean display
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # Get terminal width for proper formatting
    term_width = shutil.get_terminal_size().columns
    term_width = min(term_width, 120)  # Limit width for readability
    
    # Header
    print(f"\n{COLORS['HEADER']}{COLORS['BOLD']}{' SMART ATTENDANCE SYSTEM - GIT BRANCH DASHBOARD ':=^{term_width}}{COLORS['ENDC']}\n")
    
    # Current status
    sprint_status = get_sprint_status(data)
    current_sprint = 1
    for i, status in sprint_status.items():
        if status['pending'] > 0:
            current_sprint = i
            break
        elif status['progress'] < 100:
            current_sprint = i
    
    print(f"{COLORS['OKBLUE']}Current Status:{COLORS['ENDC']} Working on {COLORS['BOLD']}Sprint {current_sprint}: {SPRINT_CONFIG[current_sprint]['name']}{COLORS['ENDC']}")
    print(f"Active branch: {COLORS['ACTIVE']}{data['active_branch']}{COLORS['ENDC']}")
    
    # Sprint progress overview
    print(f"\n{COLORS['OKBLUE']}{COLORS['BOLD']}Sprint Progress Overview:{COLORS['ENDC']}")
    for sprint_num in sorted(sprint_status.keys()):
        status = sprint_status[sprint_num]
        sprint_name = SPRINT_CONFIG[sprint_num]['name']
        
        # Color coding for status
        if status['status'] == "Completed":
            status_color = COLORS['OKGREEN']
        elif status['status'] == "On Track":
            status_color = COLORS['OKCYAN']
        elif status['status'] == "Needs Attention":
            status_color = COLORS['WARNING']
        else:
            status_color = COLORS['FAIL']
        
        # Format the sprint line
        sprint_line = (
            f"  Sprint {sprint_num} [{status['merged']}/{status['total']}] "
            f"{draw_progress_bar(status['progress'], 20)} "
            f"{status_color}{status['status']}{COLORS['ENDC']} - {sprint_name}"
        )
        
        # Truncate if too long
        if len(sprint_line) > term_width:
            sprint_line = sprint_line[:term_width-3] + "..."
        
        print(sprint_line)
    
    # Sprint details
    print(f"\n{COLORS['OKBLUE']}{COLORS['BOLD']}Sprint Details:{COLORS['ENDC']}")
    for sprint_num in sorted(sprint_status.keys()):
        sprint_data = data['sprint_branches'][sprint_num]
        status = sprint_status[sprint_num]
        
        # Sprint header
        sprint_header = f" Sprint {sprint_num}: {SPRINT_CONFIG[sprint_num]['name']} "
        print(f"\n{COLORS['HEADER']}{sprint_header:=^{min(term_width, 60)}}{COLORS['ENDC']}")
        
        # Sprint stats
        print(f"  {status['merged']}/{status['total']} branches completed | {status['pending']} pending")
        
        # Branch details
        if sprint_data['exists']:
            print(f"\n{COLORS['OKCYAN']}  Implemented Branches:{COLORS['ENDC']}")
            for branch in sprint_data['merged']:
                print(f"    {COLORS['MERGED']}✓{COLORS['ENDC']} {branch}")
            
            if sprint_data['pending']:
                print(f"\n{COLORS['WARNING']}  Pending Branches:{COLORS['ENDC']}")
                for branch in sprint_data['pending']:
                    print(f"    {COLORS['PENDING']}→{COLORS['ENDC']} {branch}")
        else:
            print(f"  {COLORS['MISSING']}No branches implemented yet{COLORS['ENDC']}")
    
    # Special branches
    special_sections = [
        ('RELEASE BRANCHES', data['release_branches'], COLORS['RELEASE']),
        ('HOTFIX BRANCHES', data['hotfix_branches'], COLORS['HOTFIX']),
        ('SECURITY BRANCHES', data['security_branches'], COLORS['SECURITY']),
        ('TEST BRANCHES', data['test_branches'], COLORS['TEST']),
        ('CALIBRATION BRANCHES', data['calibration_branches'], COLORS['OKCYAN'])
    ]
    
    print(f"\n{COLORS['OKBLUE']}{COLORS['BOLD']}Special Branches:{COLORS['ENDC']}")
    for title, branches, color in special_sections:
        if branches:
            print(f"\n{color}{title}{COLORS['ENDC']}")
            for branch in branches:
                print(f"  • {branch}")
    
    # Actionable recommendations
    print(f"\n{COLORS['WARNING']}{COLORS['BOLD']}Actionable Recommendations:{COLORS['ENDC']}")
    
    # Recommendations for current sprint
    current_sprint_data = data['sprint_branches'][current_sprint]
    if current_sprint_data['pending']:
        print(f"  → Work on pending branches for Sprint {current_sprint}:")
        for branch in current_sprint_data['pending'][:3]:  # Show max 3 pending branches
            print(f"    - {branch}")
    
    # Check if develop branch needs updating
    try:
        subprocess.check_output(['git', 'diff', 'develop..main'], stderr=subprocess.DEVNULL)
        print(f"  → {COLORS['WARNING']}main branch is ahead of develop - consider merging main into develop{COLORS['ENDC']}")
    except subprocess.CalledProcessError:
        pass  # No diff means develop is up to date
    
    # Check for stale branches
    stale_branches = []
    for branch in data['all_branches']:
        if branch.startswith('feature/') and branch not in data['sprint_branches'][current_sprint]['planned']:
            stale_branches.append(branch)
    
    if stale_branches:
        print(f"  → {COLORS['WARNING']}Found {len(stale_branches)} stale feature branches - consider deleting{COLORS['ENDC']}")
    
    # Sprint completion check
    if current_sprint < 4 and sprint_status[current_sprint]['progress'] >= 90:
        print(f"  → {COLORS['OKGREEN']}Sprint {current_sprint} is nearly complete! Prepare for Sprint {current_sprint + 1}{COLORS['ENDC']}")
    
    # Footer
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{COLORS['OKBLUE']}Last updated: {current_time}{COLORS['ENDC']}")
    print(f"{COLORS['HEADER']}{'=' * term_width}{COLORS['ENDC']}\n")

def interactive_mode(data):
    """Interactive mode for common Git operations"""
    while True:
        print(f"\n{COLORS['OKBLUE']}{COLORS['BOLD']}Interactive Mode:{COLORS['ENDC']}")
        print("1. Create new feature branch")
        print("2. Merge pending branches to develop")
        print("3. Create release branch")
        print("4. Create hotfix branch")
        print("5. Delete merged branches")
        print("6. Refresh dashboard")
        print("7. Exit interactive mode")
        
        choice = input(f"\nSelect an option (1-7): ").strip()
        
        if choice == '1':
            # Create new feature branch
            print(f"\n{COLORS['OKCYAN']}Create New Feature Branch{COLORS['ENDC']}")
            sprint_num = input("Sprint number (1-4): ").strip()
            
            if sprint_num not in ['1', '2', '3', '4']:
                print(f"{COLORS['FAIL']}Invalid sprint number{COLORS['ENDC']}")
                continue
            
            sprint_num = int(sprint_num)
            sprint_data = data['sprint_branches'][sprint_num]
            description = input("Branch description (kebab-case): ").strip()
            
            # Find next available number
            existing_numbers = []
            for branch in sprint_data['planned']:
                match = re.search(r'feature/(\d+)[a-z]?-', branch)
                if match:
                    num = int(match.group(1))
                    existing_numbers.append(num)
            
            next_num = max(existing_numbers) + 1 if existing_numbers else 1
            branch_name = f"feature/{next_num:03d}-{description}"
            
            print(f"\nCreating branch: {COLORS['ACTIVE']}{branch_name}{COLORS['ENDC']}")
            print(f"Sprint: {COLORS['OKCYAN']}Sprint {sprint_num}: {SPRINT_CONFIG[sprint_num]['name']}{COLORS['ENDC']}")
            
            confirm = input("\nConfirm creation (y/n): ").strip().lower()
            if confirm == 'y':
                try:
                    subprocess.run(['git', 'checkout', '-b', branch_name, 'develop'], check=True)
                    print(f"{COLORS['OKGREEN']}Branch created successfully!{COLORS['ENDC']}")
                    # Update data for immediate feedback
                    data['all_branches'].append(branch_name)
                    sprint_data['exists'].append(branch_name)
                    sprint_data['pending'].append(branch_name)
                except subprocess.CalledProcessError as e:
                    print(f"{COLORS['FAIL']}Error creating branch: {e}{COLORS['ENDC']}")
        
        elif choice == '2':
            # Merge pending branches
            print(f"\n{COLORS['OKCYAN']}Merge Pending Branches to Develop{COLORS['ENDC']}")
            
            # Show pending branches by sprint
            pending_branches = []
            for sprint_num in sorted(data['sprint_branches'].keys()):
                sprint_data = data['sprint_branches'][sprint_num]
                for branch in sprint_data['pending']:
                    pending_branches.append((sprint_num, branch))
            
            if not pending_branches:
                print(f"{COLORS['WARNING']}No pending branches to merge{COLORS['ENDC']}")
                continue
            
            print("\nPending branches:")
            for i, (sprint_num, branch) in enumerate(pending_branches, 1):
                print(f"  {i}. {branch} (Sprint {sprint_num})")
            
            selection = input("\nSelect branches to merge (comma-separated numbers, or 'all'): ").strip()
            
            branches_to_merge = []
            if selection.lower() == 'all':
                branches_to_merge = [branch for _, branch in pending_branches]
            else:
                try:
                    indices = [int(x.strip()) - 1 for x in selection.split(',')]
                    branches_to_merge = [pending_branches[i][1] for i in indices if 0 <= i < len(pending_branches)]
                except (ValueError, IndexError):
                    print(f"{COLORS['FAIL']}Invalid selection{COLORS['ENDC']}")
                    continue
            
            if not branches_to_merge:
                print(f"{COLORS['WARNING']}No branches selected{COLORS['ENDC']}")
                continue
            
            print("\nBranches to merge:")
            for i, branch in enumerate(branches_to_merge, 1):
                print(f"  {i}. {branch}")
            
            confirm = input("\nConfirm merge (y/n): ").strip().lower()
            if confirm == 'y':
                try:
                    # First, checkout develop
                    subprocess.run(['git', 'checkout', 'develop'], check=True)
                    
                    # Then merge each branch
                    for branch in branches_to_merge:
                        print(f"\nMerging {branch}...")
                        subprocess.run(['git', 'merge', branch, '--no-ff'], check=True)
                        print(f"{COLORS['OKGREEN']}✓ Merged {branch} successfully{COLORS['ENDC']}")
                    
                    # Push changes
                    print("\nPushing changes to remote...")
                    subprocess.run(['git', 'push', 'origin', 'develop'], check=True)
                    print(f"{COLORS['OKGREEN']}✓ develop branch pushed successfully{COLORS['ENDC']}")
                    
                    # Update data
                    data['active_branch'] = 'develop'
                    for sprint_num, sprint_data in data['sprint_branches'].items():
                        sprint_data['pending'] = [b for b in sprint_data['pending'] if b not in branches_to_merge]
                        sprint_data['merged'].extend([b for b in branches_to_merge if b in sprint_data['planned']])
                    
                    print(f"\n{COLORS['OKGREEN']}All selected branches merged and pushed!{COLORS['ENDC']}")
                except subprocess.CalledProcessError as e:
                    print(f"{COLORS['FAIL']}Error during merge: {e}{COLORS['ENDC']}")
        
        elif choice == '3':
            # Create release branch
            print(f"\n{COLORS['OKCYAN']}Create Release Branch{COLORS['ENDC']}")
            version = input("Version number (e.g., v1.0): ").strip()
            
            if not version.startswith('v'):
                version = f"v{version}"
            
            branch_name = f"release/{version}"
            
            print(f"\nCreating release branch: {COLORS['RELEASE']}{branch_name}{COLORS['ENDC']}")
            confirm = input("\nConfirm creation (y/n): ").strip().lower()
            
            if confirm == 'y':
                try:
                    subprocess.run(['git', 'checkout', '-b', branch_name, 'develop'], check=True)
                    print(f"{COLORS['OKGREEN']}Release branch created successfully!{COLORS['ENDC']}")
                    print(f"Next steps:")
                    print(f"  1. Run final testing on {COLORS['RELEASE']}{branch_name}{COLORS['ENDC']}")
                    print(f"  2. Fix any critical issues")
                    print(f"  3. Merge to {COLORS['HEADER']}main{COLORS['ENDC']} and {COLORS['OKCYAN']}develop{COLORS['ENDC']}")
                    print(f"  4. Create tag: {COLORS['BOLD']}git tag -a {version} -m 'Release {version}'{COLORS['ENDC']}")
                except subprocess.CalledProcessError as e:
                    print(f"{COLORS['FAIL']}Error creating release branch: {e}{COLORS['ENDC']}")
        
        elif choice == '4':
            # Create hotfix branch
            print(f"\n{COLORS['OKCYAN']}Create Hotfix Branch{COLORS['ENDC']}")
            description = input("Hotfix description (kebab-case): ").strip()
            branch_name = f"hotfix/{description}"
            
            print(f"\nCreating hotfix branch: {COLORS['HOTFIX']}{branch_name}{COLORS['ENDC']}")
            print(f"Based on: {COLORS['HEADER']}main{COLORS['ENDC']} branch")
            
            confirm = input("\nConfirm creation (y/n): ").strip().lower()
            if confirm == 'y':
                try:
                    subprocess.run(['git', 'checkout', '-b', branch_name, 'main'], check=True)
                    print(f"{COLORS['OKGREEN']}Hotfix branch created successfully!{COLORS['ENDC']}")
                    print(f"Next steps:")
                    print(f"  1. Implement the fix in {COLORS['HOTFIX']}{branch_name}{COLORS['ENDC']}")
                    print(f"  2. Merge to {COLORS['HEADER']}main{COLORS['ENDC']} and {COLORS['OKCYAN']}develop{COLORS['ENDC']}")
                    print(f"  3. Create version tag if needed")
                except subprocess.CalledProcessError as e:
                    print(f"{COLORS['FAIL']}Error creating hotfix branch: {e}{COLORS['ENDC']}")
        
        elif choice == '5':
            # Delete merged branches
            print(f"\n{COLORS['OKCYAN']}Delete Merged Branches{COLORS['ENDC']}")
            
            # Find merged branches that aren't main or develop
            merged_branches = []
            for branch in data['all_branches']:
                if branch in ['main', 'develop']:
                    continue
                
                try:
                    # Check if merged into develop
                    subprocess.check_output(
                        ['git', 'branch', '--contains', branch, 'develop'],
                        stderr=subprocess.DEVNULL
                    )
                    merged_branches.append(branch)
                except subprocess.CalledProcessError:
                    pass
            
            if not merged_branches:
                print(f"{COLORS['WARNING']}No merged branches to delete{COLORS['ENDC']}")
                continue
            
            print("\nMerged branches that can be deleted:")
            for i, branch in enumerate(merged_branches, 1):
                print(f"  {i}. {branch}")
            
            selection = input("\nSelect branches to delete (comma-separated numbers, or 'all'): ").strip()
            
            branches_to_delete = []
            if selection.lower() == 'all':
                branches_to_delete = merged_branches
            else:
                try:
                    indices = [int(x.strip()) - 1 for x in selection.split(',')]
                    branches_to_delete = [merged_branches[i] for i in indices if 0 <= i < len(merged_branches)]
                except (ValueError, IndexError):
                    print(f"{COLORS['FAIL']}Invalid selection{COLORS['ENDC']}")
                    continue
            
            if not branches_to_delete:
                print(f"{COLORS['WARNING']}No branches selected{COLORS['ENDC']}")
                continue
            
            print("\nBranches to delete:")
            for i, branch in enumerate(branches_to_delete, 1):
                print(f"  {i}. {branch}")
            
            print(f"\n{COLORS['WARNING']}WARNING: This will delete branches locally and remotely!{COLORS['ENDC']}")
            confirm = input("\nConfirm deletion (y/n): ").strip().lower()
            
            if confirm == 'y':
                try:
                    # Delete locally
                    for branch in branches_to_delete:
                        subprocess.run(['git', 'branch', '-d', branch], check=True)
                        print(f"{COLORS['OKGREEN']}✓ Deleted locally: {branch}{COLORS['ENDC']}")
                    
                    # Delete remotely
                    for branch in branches_to_delete:
                        subprocess.run(['git', 'push', 'origin', '--delete', branch], check=True)
                        print(f"{COLORS['OKGREEN']}✓ Deleted remotely: {branch}{COLORS['ENDC']}")
                    
                    print(f"\n{COLORS['OKGREEN']}All selected branches deleted!{COLORS['ENDC']}")
                    
                    # Refresh data
                    return True  # Signal to refresh data
                    
                except subprocess.CalledProcessError as e:
                    print(f"{COLORS['FAIL']}Error during deletion: {e}{COLORS['ENDC']}")
        
        elif choice == '6':
            # Refresh dashboard
            print(f"\n{COLORS['OKCYAN']}Refreshing dashboard data...{COLORS['ENDC']}")
            return True  # Signal to refresh data
        
        elif choice == '7':
            # Exit interactive mode
            print(f"\n{COLORS['OKGREEN']}Exiting interactive mode{COLORS['ENDC']}")
            break
        
        else:
            print(f"{COLORS['FAIL']}Invalid option{COLORS['ENDC']}")
    
    return False  # No refresh needed

def main():
    """Main function"""
    # Parse command line arguments
    refresh = False
    interactive = False
    
    for arg in sys.argv[1:]:
        if arg == '--refresh':
            refresh = True
        elif arg == '--interactive':
            interactive = True
        elif arg in ('-h', '--help'):
            print(__doc__)
            sys.exit(0)
        else:
            print(f"{COLORS['FAIL']}Unknown argument: {arg}{COLORS['ENDC']}")
            print("Use --help for usage information")
            sys.exit(1)
    
    # Get branch data
    data = get_branch_data()
    
    # Main loop
    while True:
        # Display dashboard
        display_dashboard(data)
        
        # Check if in interactive mode
        if interactive:
            should_refresh = interactive_mode(data)
            if should_refresh:
                data = get_branch_data()
        else:
            # Normal mode - just display once
            break
    
    print(f"{COLORS['OKGREEN']}Dashboard complete!{COLORS['ENDC']}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{COLORS['WARNING']}Operation cancelled by user{COLORS['ENDC']}")
        sys.exit(1)
    except Exception as e:
        print(f"{COLORS['FAIL']}Unexpected error: {str(e)}{COLORS['ENDC']}")
        sys.exit(1)