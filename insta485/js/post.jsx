import React, { useState, useEffect } from "react";

import dayjs from "dayjs";
import relativeTime from "dayjs/plugin/relativeTime";
import utc from "dayjs/plugin/utc";

dayjs.extend(relativeTime);
dayjs.extend(utc);

// The parameter of this function is an object with a string called url inside it.
// url is a prop for the Post component.
export default function Post({ url }) {
  /* Display image and post owner of a single post */

  const [imgUrl, setImgUrl] = useState("");
  const [owner, setOwner] = useState("");
  const [ownerImgUrl, setOwnerImgUrl] = useState("");
  const [ownerShowUrl, setOwnerShowUrl] = useState("");
  const [postShowUrl, setPostShowUrl] = useState("");
  const [created, setCreated] = useState("");
  const [likes, setLikes] = useState({
    lognameLikesThis: false,
    numLikes: 0,
    url: null,
  });
  const [comments, setComments] = useState([]);
  const [postid, setPostid] = useState(null);
  const [textEntry, setTextEntry] = useState("");

  useEffect(() => {
    // Declare a boolean flag that we can use to cancel the API request.
    let ignoreStaleRequest = false;

    // Call REST API to get the post's information
    fetch(url, { credentials: "same-origin" })
      .then((response) => {
        if (!response.ok) throw Error(response.statusText);
        return response.json();
      })
      .then((data) => {
        // If ignoreStaleRequest was set to true, we want to ignore the results of the
        // the request. Otherwise, update the state to trigger a new render.
        if (!ignoreStaleRequest) {
          setImgUrl(data.imgUrl);
          setOwner(data.owner);
          setOwnerImgUrl(data.ownerImgUrl);
          setCreated(data.created);
          setLikes(data.likes);
          setComments(data.comments);
          setPostid(data.postid);
          setOwnerShowUrl(data.ownerShowUrl);
          setPostShowUrl(data.postShowUrl);
        }
      })
      .catch((error) => console.log(error));

    return () => {
      // This is a cleanup function that runs whenever the Post component
      // unmounts or re-renders. If a Post is about to unmount or re-render, we
      // should avoid updating state.
      ignoreStaleRequest = true;
    };
  }, [url]);

  const handleLike = () => {
    if (!postid) return;
    fetch(`/api/v1/likes/?postid=${postid}`, {
      method: "POST",
      credentials: "same-origin",
    })
      .then((response) => {
        if (!response.ok) throw Error(response.statusText);
        return response.json();
      })
      .then((data) => {
        setLikes((prev) => ({
          ...prev,
          lognameLikesThis: true,
          numLikes: prev.numLikes + 1,
          url: data.url,
        }));
      });
  };

  const handleUnlike = () => {
    fetch(likes.url, {
      method: "DELETE",
      credentials: "same-origin",
    }).then((response) => {
      if (!response.ok && response.status !== 204)
        throw Error(response.statusText);
      setLikes((prev) => ({
        ...prev,
        lognameLikesThis: false,
        numLikes: prev.numLikes - 1,
        url: null,
      }));
    });
  };

  const handleSubmitComment = (event) => {
    event.preventDefault(); // Prevent reload
    if (textEntry.trim() == "" || !postid) {
      // if comment is only whitespace
      // also don't load if postid is not known yet
      return;
    }
    fetch(`/api/v1/comments/?postid=${postid}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ text: textEntry }),
      credentials: "same-origin",
    })
      .then((resp) => resp.json())
      .then((newComment) => {
        setComments([...comments, newComment]);
        setTextEntry("");
      });
  };

  const handleDeleteComment = (commentID) => {
    fetch(`/api/v1/comments/${commentID}/`, { method: "DELETE" }).then(() => {
      setComments(comments.filter((c) => c.commentid !== commentID));
    });
  };

  // Render post image and post owner
  return (
    <div className="post">
      <a href={ownerShowUrl} className="image-link">
        <img
          src={ownerImgUrl || null}
          alt={owner}
          style={{ width: "40px", height: "40px" }}
        />
        {owner}
      </a>
      <a className="timestamp" href={postShowUrl}>
        <PostTimestamp created={created} />
      </a>{" "}
      <br></br>
      <img
        src={imgUrl || null}
        alt="post_image"
        onDoubleClick={() => {
          if (!likes.lognameLikesThis) handleLike();
        }}
      />
      <div>
        {likes.numLikes} {likes.numLikes === 1 ? "like" : "likes"}
      </div>
      <div className="comments">
        {comments.map((comment) => (
          <div key={comment.commentid} className="comment">
            <a href={comment.ownerShowUrl}>{comment.owner}</a>
            {": "}
            <span data-testid="comment-text">{comment.text}</span>

            {comment.lognameOwnsThis && (
              <button
                type="button"
                data-testid="delete-comment-button"
                onClick={() => handleDeleteComment(comment.commentid)}
              >
                Delete
              </button>
            )}
          </div>
        ))}
      </div>
      <button
        onClick={likes.lognameLikesThis ? handleUnlike : handleLike}
        data-testid="like-unlike-button"
        disabled={postid === null}
      >
        {likes.lognameLikesThis ? "Unlike" : "Like"}
      </button>
      {postid && (
        <form data-testid="comment-form" onSubmit={handleSubmitComment}>
          <input
            type="text"
            value={textEntry}
            onChange={(e) => setTextEntry(e.target.value)}
          />
          <button type="submit" data-testid="comment-submit-button">
            Post
          </button>
        </form>
      )}
    </div>
  );
}

function PostTimestamp({ created }) {
  const [, setNow] = useState(dayjs());

  useEffect(() => {
    const interval = setInterval(() => setNow(dayjs()), 60000);
    return () => clearInterval(interval);
  }, []);

  return (
    <span data-testid="post-time-ago">
      {dayjs.utc(created).local().fromNow()}
    </span>
  );
}
