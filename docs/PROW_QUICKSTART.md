# Prow Commands Quick Start Guide

This is a quick reference guide to get you started with Prow commands in the BHV repository.

## What are Prow Commands?

Prow commands are bot-driven commands that you can use by commenting on issues or pull requests. They help automate common tasks like labeling, assigning, and running CI tests.

## Basic Usage

Simply comment on an issue or PR with a command starting with `/`:

```
/command [arguments]
```

## Most Common Commands

### For All Contributors

**Get help:**
```
/help
```

**Rerun failed tests:**
```
/retest
```

**Run specific tests:**
```
/test all
/test integration
/lint
```

**Request more info:**
```
/needs-info
```

### For Organization Members

**Assign yourself to an issue:**
```
/assign
```

**Assign someone else:**
```
/assign @username
```

**Label an issue as a bug:**
```
/kind bug
```

**Set priority:**
```
/priority p1
```

**Set area:**
```
/area database
```

**Approve code changes (LGTM):**
```
/lgtm
```

### For Maintainers Only

**Approve PR for merge:**
```
/approve
```

**Block a PR from merging:**
```
/hold
```

**Allow merge again:**
```
/unhold
```

**Close an issue:**
```
/close
```

**Mark as good for newcomers:**
```
/good-first-issue
```

## Common Workflows

### Triaging a New Bug Report

```
/kind bug
/area api
/priority p2
/assign @developer-name
```

### Reviewing a Pull Request

If code looks good:
```
/lgtm
/approve
```

If changes needed:
```
/hold
Please address the following issues:
- Fix linting errors
- Add unit tests
```

### Running Tests After Fix

```
/retest
```

Or run specific tests:
```
/test integration
/test security
```

### Labeling a Feature Request

```
/kind feature
/area frontend
/priority p3
```

## Issue Types (/kind)

- `bug` - Something is broken
- `feature` - New functionality request
- `enhancement` - Improvement to existing feature
- `documentation` - Documentation changes
- `question` - Question about the project
- `cleanup` - Code refactoring/cleanup
- `security` - Security-related
- `performance` - Performance improvement

## Priority Levels (/priority)

- `p0` - Critical, fix immediately
- `p1` - High priority, fix soon
- `p2` - Medium priority, normal timeline
- `p3` - Low priority, nice to have

## Areas (/area)

- `api` - API endpoints and logic
- `auth` - Authentication/authorization
- `database` - Database operations
- `frontend` - User interface
- `storage` - File storage system
- `testing` - Test infrastructure
- `ci-cd` - CI/CD pipelines
- `documentation` - Documentation
- `security` - Security features

## Test Jobs (/test)

- `/test all` - Complete test suite
- `/test tests` - Unit tests only
- `/test integration` - Integration tests
- `/test db` - Database tests
- `/test security` - Security scans
- `/lint` - Run all linters

## Multiple Commands

You can combine commands in one comment:

```
/kind feature
/area api
/priority p2
/assign @developer
```

## Tips

1. Commands must start with `/` on a new line
2. Commands are case-sensitive for arguments (use lowercase)
3. Use `/help` anytime to see available commands
4. Commands execute immediately when you post the comment
5. You'll get feedback if a command fails or you lack permissions

## Permission Levels

| Permission Level | Who | Can Use |
|-----------------|-----|---------|
| Anyone | All users | `/help`, `/retest`, `/test`, `/lint`, `/needs-info` |
| Org Members | KathiraveluLab members | Above + `/assign`, `/kind`, `/area`, `/priority`, `/lgtm` |
| Maintainers | Write/admin access | Above + `/approve`, `/hold`, `/close`, `/reopen` |

## Examples

### Example 1: I found a bug

You: Open an issue describing the bug

Maintainer:
```
/kind bug
/area database
/priority p1
/assign @database-expert
```

### Example 2: My PR has failing tests

You:
```
Fixed the linting issues
/retest
```

### Example 3: Requesting review

You:
```
/ready
This PR is ready for review!
```

Reviewer:
```
/lgtm
Looks great!
```

Maintainer:
```
/approve
```

### Example 4: Working on an issue

You:
```
/assign
I'll work on this issue
```


## Next Steps

1. Try using `/help` on an issue or PR
2. Use `/assign` to assign yourself to an issue
3. Try labeling with `/kind` and `/area`
4. Read the full documentation for advanced usage