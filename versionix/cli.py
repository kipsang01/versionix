import os
import sys
import argparse

from versionix.vsx import Versionix


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Version Control System')
    subparsers = parser.add_subparsers(dest='command', help='VCS commands')

    # Init command
    init_parser = subparsers.add_parser('init', help='Initialize a new repository')
    init_parser.add_argument('path', nargs='?', default='.', help='Path to initialize repository')

    # Add command
    add_parser = subparsers.add_parser('add', help='Stage files for commit')
    add_parser.add_argument('files', nargs='+', help='Files to stage')

    # Commit command
    commit_parser = subparsers.add_parser('commit', help='Commit staged changes')
    commit_parser.add_argument('-m', '--message', required=True, help='Commit message')

    # Log command
    subparsers.add_parser('log', help='Show commit history')

    # Status command
    subparsers.add_parser('status', help='Show repository status')

    # Branch command
    branch_parser = subparsers.add_parser('branch', help='Create or list branches')
    branch_parser.add_argument('name', nargs='?', help='Branch name to create')

    # Checkout command
    checkout_parser = subparsers.add_parser('checkout', help='Checkout a branch')
    checkout_parser.add_argument('name', help='Branch name to checkout')

    # Diff command
    diff_parser = subparsers.add_parser('diff', help='Show differences between branches')
    diff_parser.add_argument('branch1', help='First branch')
    diff_parser.add_argument('branch2', help='Second branch')

    # Merge command
    merge_parser = subparsers.add_parser('merge', help='Show differences between branches')
    merge_parser.add_argument('branch1', help='Source branch')
    merge_parser.add_argument('branch2', help='Target branch')

    # Clone command
    clone_parser = subparsers.add_parser('clone', help='Clone a repository')
    clone_parser.add_argument('source', help='Source repository path')
    clone_parser.add_argument('destination', help='Destination path')

    args = parser.parse_args()

    try:
        match args.command:
            case 'init':
                Versionix(args.path)
                print(f"Initialized empty VSX repository in {os.path.abspath(args.path)}")

            case 'add':
                vsx = Versionix()
                for file in args.files:
                    vsx.add(file)

            case 'commit':
                vsx = Versionix()
                vsx.commit(args.message)

            case 'log':
                vsx = Versionix()
                vsx.log()

            case 'status':
                vsx = Versionix()
                vsx.status()

            case 'branch':
                vsx = Versionix()
                vsx.branch(args.name)

            case 'checkout':
                vsx = Versionix()
                vsx.checkout(args.name)

            case 'diff':
                vsx = Versionix()
                vsx.diff(args.branch1, args.branch2)

            case 'merge':
                vsx = Versionix()
                vsx.merge(args.branch1, args.branch2)

            case 'clone':
                vsx = Versionix(args.source)
                vsx.clone(args.destination)

            case _:
                parser.print_help()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
