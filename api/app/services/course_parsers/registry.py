"""Parser registry — curriculum type → fetch ladder → structured lessons."""

from __future__ import annotations



import re



from app.services.course_parsers.article_hub import parse_article_hub_html

from app.services.course_parsers.connector_profiles import fetch_ladder_for, get_connector_profile

from app.services.course_parsers.fetch import FetchResult, fetch_html, guess_hub_path_prefix

from app.services.course_parsers.lms_catalog import parse_coursera_catalog_html, parse_udemy_catalog_html

from app.services.course_parsers.quality import score_article_hub, score_youtube_curriculum

from app.services.course_parsers.types import CourseLesson, ParseAttempt, ParseResult

from app.services.course_parsers.youtube_curriculum import (

    is_youtube_playlist_url,

    parse_youtube_curriculum_html,

    parse_youtube_curriculum_json_ld,

    parse_youtube_playlist_ytdlp,

)



PARSER_VERSION = "course.registry.v1"





def _slug_prefix(url: str, fallback: str = "course") -> str:

    m = re.search(r"https?://[^/]+/([^/?#]+)", url or "")

    return re.sub(r"[^a-z0-9]+", "-", (m.group(1) if m else fallback).lower()).strip("-")[:40] or fallback





def _merge_unique(primary: list[CourseLesson], secondary: list[CourseLesson]) -> list[CourseLesson]:

    seen = {((l.url or l.video_url or "").rstrip("/").lower()) for l in primary}

    out = list(primary)

    n = len(out)

    for lesson in secondary:

        key = (lesson.url or lesson.video_url or "").rstrip("/").lower()

        if key and key in seen:

            continue

        if key:

            seen.add(key)

        n += 1

        lesson.order_index = n

        out.append(lesson)

    return out





def _parse_html_for_type(

    html: str,

    *,

    url: str,

    curriculum_type: str,

    id_prefix: str,

) -> ParseResult:

    ctype = (curriculum_type or "website").strip().lower()

    result = ParseResult(parser_key=ctype)

    lessons: list[CourseLesson] = []

    course_title: str | None = None

    extra_anomalies: list[str] = []



    if ctype == "youtube_curriculum":

        lessons, course_title = parse_youtube_curriculum_html(html, url=url, id_prefix=id_prefix)

        if len(lessons) < 3:

            lessons = _merge_unique(

                lessons,

                parse_youtube_curriculum_json_ld(html, url=url, id_prefix=id_prefix),

            )

        score, anomalies = score_youtube_curriculum(lessons)

        result.parser_key = "course.youtube_curriculum.dom.v1"

    elif ctype == "article_hub":

        hub_prefix = guess_hub_path_prefix(url)

        lessons, course_title = parse_article_hub_html(

            html,

            hub_url=url,

            path_prefix=hub_prefix,

            id_prefix=id_prefix,

        )

        score, anomalies = score_article_hub(lessons)

        result.parser_key = "course.article_hub.dom.v1"

    elif ctype == "coursera_catalog":

        lessons, extra_anomalies = parse_coursera_catalog_html(html, url=url, id_prefix=id_prefix)

        score, anomalies = score_article_hub(lessons)

        result.parser_key = "course.coursera.catalog.v1"

    elif ctype == "udemy_catalog":

        lessons, extra_anomalies = parse_udemy_catalog_html(html, url=url, id_prefix=id_prefix)

        score, anomalies = score_article_hub(lessons)

        result.parser_key = "course.udemy.catalog.v1"

    elif ctype == "website":

        yt, course_title = parse_youtube_curriculum_html(html, url=url, id_prefix=id_prefix)

        hub_prefix = guess_hub_path_prefix(url)

        art, _ = parse_article_hub_html(

            html,

            hub_url=url,

            path_prefix=hub_prefix,

            id_prefix=id_prefix,

        )

        lessons = _merge_unique(yt, art)

        score_yt, an_yt = score_youtube_curriculum(yt)

        score_art, an_art = score_article_hub(art)

        score = max(score_yt, score_art) if lessons else 0

        anomalies = list({*an_yt, *an_art})

        if not lessons:

            anomalies.append("EXTRACT_SCHEMA_MISMATCH")

        result.parser_key = "course.website.auto.v1"

    else:

        result.anomalies.append("EXTRACT_SCHEMA_MISMATCH")

        return result



    result.lessons = lessons

    result.course_title = course_title

    result.quality_score = score

    result.anomalies.extend(extra_anomalies)

    result.anomalies.extend(anomalies)

    return result





def discover_curriculum(

    url: str,

    curriculum_type: str,

    *,

    id_prefix: str | None = None,

) -> ParseResult:

    """

    Run fetch ladder + page-type parser for a curriculum URL.

    curriculum_type: youtube_curriculum | article_hub | coursera_catalog | udemy_catalog | website

    """

    url = (url or "").strip()

    if not url.startswith("http"):

        raise ValueError("Discover requires an http(s) source URL")



    ctype = (curriculum_type or "website").strip().lower()

    prefix = id_prefix or _slug_prefix(url)

    profile = get_connector_profile(ctype)



    if is_youtube_playlist_url(url) or ctype == "youtube_playlist":

        try:

            lessons, course_title = parse_youtube_playlist_ytdlp(url, id_prefix=prefix)

            score, anomalies = score_youtube_curriculum(lessons)

            result = ParseResult(parser_key="course.youtube_playlist.ytdlp.v1")

            result.lessons = lessons

            result.course_title = course_title

            result.quality_score = score

            result.anomalies.extend(anomalies)

            result.fetch_mode = "ytdlp"

            result.attempts.append(

                ParseAttempt(

                    parser_key=result.parser_key,

                    fetch_mode="ytdlp",

                    lessons_found=len(lessons),

                )

            )

            return result

        except Exception as exc:

            result = ParseResult(parser_key="course.youtube_playlist.ytdlp.v1")

            result.anomalies.append("YTDLP_EXTRACT_FAILED")

            result.attempts.append(

                ParseAttempt(

                    parser_key=result.parser_key,

                    fetch_mode="ytdlp",

                    error=str(exc),

                )

            )

            return result



    best: ParseResult | None = None

    last_err: str | None = None



    for prefer_js in fetch_ladder_for(ctype):

        try:

            fetch = fetch_html(url, prefer_js=prefer_js)

        except Exception as exc:

            last_err = str(exc)

            continue



        parsed = _parse_html_for_type(

            fetch.html,

            url=fetch.final_url or url,

            curriculum_type=ctype,

            id_prefix=prefix,

        )

        parsed.fetch_mode = fetch.mode

        parsed.attempts.append(

            ParseAttempt(

                parser_key=parsed.parser_key,

                fetch_mode=fetch.mode,

                http_status=fetch.status_code,

                lessons_found=len(parsed.lessons),

            )

        )

        if best is None or len(parsed.lessons) > len(best.lessons):

            best = parsed

        if parsed.lessons:

            break



    if best is None:

        result = ParseResult(parser_key=ctype)

        result.anomalies.append("RENDER_TIMEOUT")

        if last_err:

            result.attempts.append(ParseAttempt(parser_key=ctype, fetch_mode="failed", error=last_err))

        return result



    if (

        not best.lessons

        and ctype != "website"

        and profile.allow_website_fallback

    ):

        fallback = discover_curriculum(url, "website", id_prefix=prefix)

        if fallback.lessons:

            fallback.anomalies.insert(0, f"FALLBACK_FROM_{ctype}")

            return fallback



    return best





def lessons_to_dicts(lessons: list[CourseLesson]) -> list[dict]:

    return [

        {

            "id": lesson.id,

            "title": lesson.title,

            "category": lesson.category,

            "kind": lesson.kind,

            "has_video": lesson.has_video,

            "video_url": lesson.video_url,

            "url": lesson.url or lesson.video_url,

            "description": lesson.description,

            "order_index": lesson.order_index,

            "duration_seconds": lesson.duration_seconds,

        }

        for lesson in lessons

    ]

