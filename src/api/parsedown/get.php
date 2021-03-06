<?php
    header('Content-Type: text/html; charset=UTF-8');
    include "./parsedown.php";
    
    $text = $_POST['md'];

    $parsedown = new Parsedown();
    $parsedown->setSafeMode(true);

    $result = $parsedown->text($text);

    // Custom Markdown
    $result = preg_replace(
        '/@gif\[.*\"(https?:\/\/.*\.mp4)\".*\]/',
        '<video autoplay muted loop><source src="$1" type="video/mp4"/></video>',
        $result
    );
    $result = preg_replace(
        '/@youtube\[(.*)\]/',
        '<iframe width="100%" height="315" src="https://www.youtube.com/embed/$1" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>',
        $result
    );

    // Allow Markup
    $result = preg_replace('/&lt;br\/?&gt;/', '<br>', $result);
    $result = preg_replace('/&lt;(\/)?center&gt;/', '<$1center>', $result);
    
    echo $result;
?>