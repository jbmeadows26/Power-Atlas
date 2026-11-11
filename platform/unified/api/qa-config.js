/* Public client configuration. Token is a PostHog *project* token, not a secret.
   Values are read from Vercel environment and never stored in git. */
module.exports = function handler(req,res){
  res.setHeader("Cache-Control","no-store");
  if(req.method!=="GET")return res.status(405).json({enabled:false});
  const token=process.env.POSTHOG_PUBLIC_TOKEN||"";
  const host=process.env.POSTHOG_API_HOST||"";
  if(!/^phc_[A-Za-z0-9_-]{10,}$/.test(token)||!/^https:\/\/(us|eu)\.i\.posthog\.com$/.test(host)){
    return res.status(200).json({enabled:false});
  }
  return res.status(200).json({enabled:true,token,host});
};
