# Website Technical Setup Documentation

## Repository: website-new/
GitHub: `git@github.com:jchopenclawhu-web/see-website.git`

## SSH Authentication
The repo is configured to use a dedicated SSH key for GitHub authentication:
- **SSH Key:** `~/.ssh/github_openclaw` (ed25519)
- **Config:** `git config core.sshCommand "ssh -i ~/.ssh/github_openclaw"`
- **Result:** Just use `git push` — no extra flags needed

## Site Structure
```
website-new/
├── index.html          # Main landing page
├── vocabulary.html     # Vocabulary page (Basic, L1, L2)
├── songs.html          # Monthly Songs page
├── audiobooks.html     # Audiobooks page (Pre-K, Basic, L1-L4)
├── images/
│   ├── background.png       # Optimized hero background (~1.6MB)
│   ├── background_original.png  # Original (excluded from git, ~6.5MB)
│   └── sandy.png            # Logo/profile image
└── .gitignore
```

## Deployment
This is a **GitHub Pages** site. Changes pushed to `main` branch are automatically deployed.

## Recent Major Updates
- **2026-03-24:** Audiobooks page complete with all data from Google Sheets
- **2026-03-22:** Monthly Songs page with YouTube embeds
- **2026-03-20:** Vocabulary page created

## Future Automation Notes
- SSH authentication is fully configured — no manual steps needed
- Large original images should be optimized before committing
- Use `.gitignore` to exclude source files that have been processed

## Commands for Reference
```bash
# Check status
git status

# Add and commit
git add .
git commit -m "Description"

# Push (SSH key auto-configured)
git push

# View recent commits
git log --oneline -10
```
