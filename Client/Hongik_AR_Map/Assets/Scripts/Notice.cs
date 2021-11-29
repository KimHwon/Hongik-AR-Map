using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

public class Notice : MonoBehaviour
{
    [Header("Notice")]
    public GameObject box;
    public Text text;
    public Animator noticeAnimation;

    private WaitForSeconds on = new WaitForSeconds(2.0f);
    private WaitForSeconds off = new WaitForSeconds(0.3f);

    // Start is called before the first frame update
    void Start()
    {
        box.SetActive(false);
    }

    public void SetNotice(string message)
    {
        text.text = message;
        box.SetActive(false);
        StopAllCoroutines();
        StartCoroutine("DisplayNotice");
    }

    IEnumerator DisplayNotice()
    {
        box.SetActive(true);
        noticeAnimation.SetBool("NoticeOn", true);
        yield return on;
        noticeAnimation.SetBool("NoticeOn", false);
        yield return off;
        box.SetActive(false);
    }
}
