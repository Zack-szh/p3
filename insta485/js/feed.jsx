import React, { useState, useEffect, useCallback } from "react";
import Post from "./post";
import InfiniteScroll from "react-infinite-scroll-component";

export default function Feed() {
  const [posts, setPosts] = useState([]);
  const [nextUrl, setNextUrl] = useState("/api/v1/posts/");
  const [morePosts, setMorePosts] = useState(true);
  // for infinite scrolling, indicate if more posts left

  const fetchPosts = useCallback(() => {
    if (!nextUrl) {
      setMorePosts(false);
      return;
    }

    // same-origin ensures the session cookies are sent to API
    fetch(nextUrl, { credentials: "same-origin" })
      .then((res) => res.json())
      // NOTE: we have to create a new array instead of modifying existing one.
      // React does shallow comparasion, should not mutate states directly
      // if simply append the list, might not trigger rerender
      .then((data) => {
        //setPosts((posts) => [...posts, ...data.results]);
        setPosts((prevPosts) => {
          // filter the posts so no duplicates appear
          const newPosts = data.results.filter(
            (post) => !prevPosts.some((prev) => prev.postid === post.postid),
          );
          return [...prevPosts, ...newPosts];
        });

        setNextUrl(data.next || "");
      })

      .catch((err) => {
        console.error("Error fetching posts: ", err);
        setMorePosts(false); // no more posts
      });
  }, [nextUrl]);

  useEffect(() => {
    fetchPosts();
  }, [fetchPosts]);

  return (
    <InfiniteScroll
      dataLength={posts.length}
      next={fetchPosts} // Fetch more posts on scroll
      hasMore={morePosts}
      loader={<p>Loading more posts...</p>}
      endMessage={<p>You have reached the end of the feed!</p>}
    >
      <div className="feed">
        {posts.length === 0 && <p>Loading feed...</p>}
        {posts.map((post) => (
          <div key={post.postid}>
            <Post url={post.url} />
            <br />
            <br />
          </div>
        ))}
      </div>
    </InfiniteScroll>
  );
}
