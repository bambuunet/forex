;(function($){ $(function(){

/*::;;;;::*ﾟ*::;;;;::*ﾟ*::;;;;::*ﾟ*::;;;;::*ﾟ*::;;;;::*ﾟ*::;;;;::*
    click
 *::;;;;::*ﾟ*::;;;;::*ﾟ*::;;;;::*ﾟ*::;;;;::*ﾟ*::;;;;::*ﾟ*::;;;;::*/
  $('.globalNav').find('span').on('click mouseover', function(){
    $('.globalNav-pulldown').css({
      'display': 'none'
    });
    $(this).next().css({
      'display': 'block',
    });
  });

  $('.globalNav-pulldown').on('mouseleave', function(){
    $('.globalNav-pulldown').css({
      'display': 'none'
    });
    console.log('a')
  });


}); })(jQuery);
