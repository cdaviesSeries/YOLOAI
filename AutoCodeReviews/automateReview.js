async function automateReview(){
    // necessary constants
    const fs = require('fs');
    const aiComments = JSON.parse(fs.readFileSync('${{ github.workspace }}/review.json', 'utf8'));
    const botUser = 'github-actions[bot]'; // GitHub Actions user
    const owner = context.repo.owner;
    const repo = context.repo.repo;
    const pull_number = context.payload.pull_request.number;

    //Helpers first
    async function deleteReviewComments(review_id) {
        let page = 1;
        const per_page = 100;
        let comments;
        
        do {
            comments = await github.rest.pulls.listReviewComments({
                owner,
                repo,
                pull_number,
                review_id,
                page,
                per_page,
            });
            
            for (const comment of comments.data) {
                if (comment.user.login === botUser) {
                    console.log(`Deleting review comment #${comment.id} by ${botUser}`);
                    await github.rest.pulls.deleteReviewComment({
                        owner,
                        repo,
                        comment_id: comment.id,
                    });
                }
            }
            
            page += 1;
        } while (comments.data.length === per_page);
    }

    async function cleanPreviousReviews() {
        const reviews = await github.rest.pulls.listReviews({
            owner,
            repo,
            pull_number,
        });
        
        for (const review of reviews.data) {
            if (review.user.login === botUser && review.state === "COMMENT") {
                console.log(`Deleting comments of review #${review.id} by ${botUser}`);
                deleteReviewComments(review.id);
                
                console.log(`Dismissing review #${review.id} by ${botUser}`);
                await github.rest.pulls.dismissReview({
                    owner,
                    repo,
                    pull_number,
                    review_id: review.id,
                    message: "Dismissing my previous review because of an update to this PR."
                });
            }
        }
        
    }

    // Actual update logic.
    // You may want to move this within the if statement
    // In case it keeps adding reviews on every update/push to the branch.
    cleanPreviousReviews();
    if (aiComments.length > 0) {
        await github.rest.pulls.createReview({
            owner: context.repo.owner,
            repo: context.repo.repo,
            pull_number: context.payload.pull_request.number,
            commit_id: '${{ github.event.pull_request.head.sha }}',
            body: "I found a couple of issues, see these comments.",
            event: "COMMENT",
            comments: aiComments,
        });
    } else {
        await github.rest.pulls.createReview({
            owner: context.repo.owner,
            repo: context.repo.repo,
            pull_number: context.payload.pull_request.number,
            commit_id: '${{ github.event.pull_request.head.sha }}',
            body: "LGTM!",
            event: "COMMENT",
        })
    }
}


