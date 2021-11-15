using System.Collections;
using System.Collections.Generic;
using UnityEngine;

using System;
using System.Net;
using System.Net.Sockets;
using System.Runtime.InteropServices;
using System.IO;
using System.Text;

public class Cam : MonoBehaviour
{
    WebCamTexture webCamTexture;
    Socket image_sock;
    Socket message_sock;

    const string IP = "192.168.0.100";
    
    // Start is called before the first frame update
    void Start()
    {
        webCamTexture = new WebCamTexture();
        GetComponent<Renderer>().material.mainTexture = webCamTexture; //Add Mesh Renderer to the GameObject to which this script is attached to
        webCamTexture.Play();

        //SetText("DebugText", webCamTexture.width.ToString() + ", " + webCamTexture.height.ToString());

        image_sock = new Socket(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp);
        IPEndPoint ep1 = new IPEndPoint(IPAddress.Parse(IP), 50020);
        image_sock.Connect(ep1);

        message_sock = new Socket(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp);
        IPEndPoint ep2 = new IPEndPoint(IPAddress.Parse(IP), 50021);
        message_sock.Connect(ep2);

        StartCoroutine("TakePhoto");
    }

    // Update is called once per frame
    void Update()
    {
        if (Input.touchCount > 0)
        {
            byte[] bytes = Encoding.UTF8.GetBytes("save");
            message_sock.Send(bytes);
        }
    }

    void OnApplicationQuit() {
        image_sock.Close();
        message_sock.Close();
    }

    IEnumerator TakePhoto()  // Start this Coroutine on some button click
    {
        while (true) {
            yield return new WaitForSeconds(.1f);
            // NOTE - you almost certainly have to do this here:
            yield return new WaitForEndOfFrame(); 

            // it's a rare case where the Unity doco is pretty clear,
            // http://docs.unity3d.com/ScriptReference/WaitForEndOfFrame.html
            // be sure to scroll down to the SECOND long example on that doco page 

            Texture2D photo = new Texture2D(webCamTexture.width, webCamTexture.height);
            photo.SetPixels(webCamTexture.GetPixels());
            photo.Apply();

            try
            {
                //Encode to a PNG
                byte[] bytes = photo.EncodeToJPG();
                //Write out the PNG. Of course you have to substitute your_path for something sensible

                /* Color[] pixels = photo.GetPixels();
                byte[] bytes = new byte[webCamTexture.width * webCamTexture.height * 3];
                int pixel = 0;
                for (int i = 0, index = 0; i < webCamTexture.height; ++i)
                {
                    for (int j = 0; j < webCamTexture.width; ++j)
                    {
                        var color = pixels[pixel++];
                        bytes[index++] = (byte)color.r;
                        bytes[index++] = (byte)color.g;
                        bytes[index++] = (byte)color.b;
                    }
                } */

                byte[] size = BitConverter.GetBytes(bytes.Length);
                SetText("DebugText", bytes.Length.ToString());

                //image_sock.Send(size, SocketFlags.None);
                //image_sock.Send(BitConverter.GetBytes(webCamTexture.width), SocketFlags.None);
                //image_sock.Send(BitConverter.GetBytes(webCamTexture.height), SocketFlags.None);
                image_sock.Send(bytes, SocketFlags.None);
            }
            catch (Exception e)
            {
                SetText("DebugText", e.ToString());
            }
        }
    }

    void SetText(string name, string str) {
        GameObject debugText = GameObject.Find(name);
        if (debugText != null) {
            TextMesh textMesh = debugText.GetComponent("TextMesh") as TextMesh;
            if (textMesh != null) {
                textMesh.text = str;
            }
        }
    }

    byte[] Color32ArrayToByteArray(Color32[] colors)
    {
        if (colors == null || colors.Length == 0)
            return null;

        int lengthOfColor32 = Marshal.SizeOf(typeof(Color32));
        int length = lengthOfColor32 * colors.Length;
        byte[] bytes = new byte[length];

        GCHandle handle = default(GCHandle);
        try
        {
            handle = GCHandle.Alloc(colors, GCHandleType.Pinned);
            IntPtr ptr = handle.AddrOfPinnedObject();
            Marshal.Copy(ptr, bytes, 0, length);
        }
        finally
        {
            if (handle != default(GCHandle))
                handle.Free();
        }

        return bytes;
    }
}
